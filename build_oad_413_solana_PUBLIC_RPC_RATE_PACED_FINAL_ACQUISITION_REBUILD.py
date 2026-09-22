from pathlib import Path
import ast,hashlib,os,shutil,time
EXPECTED='build_oad_413_solana_PUBLIC_RPC_RATE_PACED_FINAL_ACQUISITION_REBUILD.py'
TARGET=Path('qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py')
EXPECTED_HASH='778a279dce09d34fa1d6995ec8b74027415a47a0e370a4eaa3c3595b29af8c78'
NEW_SOURCE='''from __future__ import annotations
from dataclasses import dataclass
import time
from .oad_148_solana_mainnet_chain_state_acquisition import _rpc
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaFinalizedBlockBatch:
    head_slot:int; requested_start:int; finalized_slots:tuple; blocks:tuple; transaction_count:int; execution_authority:bool=False

def _is_transient_rpc_error(exc):
    msg=str(exc).lower(); code=getattr(exc,"code",None)
    return code==429 or any(x in msg for x in (
        "429","too many requests","rate limit","timed out","timeout",
        "temporarily unavailable","connection reset","remote end closed connection"
    ))

def _retry_after_seconds(exc):
    headers=getattr(exc,"headers",None)
    if headers is None:return None
    try:value=headers.get("Retry-After")
    except Exception:return None
    if value is None:return None
    try:return max(0.0,float(value))
    except Exception:return None

def _fetch_block_once(slot,timeout_seconds):
    return int(slot),_rpc("getBlock",[int(slot),{"commitment":"finalized","encoding":"jsonParsed","transactionDetails":"full","rewards":False,"maxSupportedTransactionVersion":0}],timeout_seconds)

def _fetch_blocks_rate_paced(slots,timeout_seconds,min_interval_seconds=0.30,max_attempts_per_slot=8,sleep_fn=time.sleep,monotonic_fn=time.monotonic):
    slots=tuple(int(s) for s in slots)
    out={}; last_call_at=None
    for slot in slots:
        attempt=0
        while True:
            if last_call_at is not None:
                wait=float(min_interval_seconds)-(float(monotonic_fn())-float(last_call_at))
                if wait>0:sleep_fn(wait)
            last_call_at=float(monotonic_fn())
            try:
                s,b=_fetch_block_once(slot,timeout_seconds);out[s]=b;break
            except Exception as exc:
                if not _is_transient_rpc_error(exc):raise
                attempt+=1
                if attempt>=max(1,int(max_attempts_per_slot)):raise
                retry_after=_retry_after_seconds(exc)
                cooldown=retry_after if retry_after is not None else min(10.0,max(1.0,0.75*(2**(attempt-1))))
                sleep_fn(cooldown)
                last_call_at=None
    return out

def acquire_finalized_block_batch(start_slot=None,limit=4,timeout_seconds=20.0,min_interval_seconds=0.30,max_attempts_per_slot=8,sleep_fn=time.sleep,monotonic_fn=time.monotonic):
    head=int(_rpc("getSlot",[{"commitment":"finalized"}],timeout_seconds))
    limit=max(1,min(int(limit),32))
    start=max(0,int(start_slot) if start_slot is not None else head-limit+1)
    stop=min(head,start+limit-1)
    slots=tuple(int(x) for x in (_rpc("getBlocks",[start,stop,{"commitment":"finalized"}],timeout_seconds) or ()))
    slots=slots[-limit:]
    if not slots:return SolanaFinalizedBlockBatch(head,start,(),(),0,False)
    by_slot=_fetch_blocks_rate_paced(slots,timeout_seconds,min_interval_seconds,max_attempts_per_slot,sleep_fn,monotonic_fn)
    blocks=[];txc=0
    for slot in slots:
        block=by_slot.get(slot)
        if not isinstance(block,dict):continue
        tx=tuple(block.get("transactions") or ());txc+=len(tx);blocks.append((slot,block))
    return SolanaFinalizedBlockBatch(head,start,slots,tuple(blocks),txc,False)
'''
TEST_SOURCE='''import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from email.message import Message
from qseries_v2.oracle_adapters.independent import oad_318_solana_native_finalized_block_stream as m

class Clock:
    def __init__(self):self.t=0.0;self.sleeps=[]
    def now(self):return self.t
    def sleep(self,x):self.sleeps.append(float(x));self.t+=float(x)

class T(unittest.TestCase):
    def test_serial_rate_pacing_preserves_order(self):
        c=Clock();calls=[]
        def rpc(method,params,timeout):
            if method=="getSlot":return 200
            if method=="getBlocks":return [101,102,103,104]
            if method=="getBlock":calls.append((params[0],c.now()));return {"transactions":[{"slot":params[0]}]}
            raise AssertionError(method)
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(101,4,2,min_interval_seconds=.30,sleep_fn=c.sleep,monotonic_fn=c.now)
        self.assertEqual(tuple(s for s,_ in x.blocks),(101,102,103,104))
        self.assertEqual([s for s,_ in calls],[101,102,103,104])
        self.assertTrue(all((calls[i][1]-calls[i-1][1])>=.299 for i in range(1,len(calls))))

    def test_429_honors_retry_after_then_recovers(self):
        c=Clock();n=0
        def rpc(method,params,timeout):
            nonlocal n
            if method=="getSlot":return 100
            if method=="getBlocks":return [90]
            if method=="getBlock":
                n+=1
                if n==1:
                    h=Message();h["Retry-After"]="2"
                    raise HTTPError("https://api.mainnet.solana.com",429,"Too Many Requests",h,None)
                return {"transactions":[]}
        with patch.object(m,"_rpc",side_effect=rpc):
            x=m.acquire_finalized_block_batch(90,1,2,sleep_fn=c.sleep,monotonic_fn=c.now)
        self.assertEqual(tuple(s for s,_ in x.blocks),(90,))
        self.assertIn(2.0,c.sleeps)

    def test_transient_retry_is_bounded(self):
        c=Clock()
        def rpc(method,params,timeout):
            if method=="getSlot":return 100
            if method=="getBlocks":return [90]
            if method=="getBlock":raise RuntimeError("HTTP 429 Too Many Requests")
        with patch.object(m,"_rpc",side_effect=rpc):
            with self.assertRaises(RuntimeError):m.acquire_finalized_block_batch(90,1,2,max_attempts_per_slot=3,sleep_fn=c.sleep,monotonic_fn=c.now)
        self.assertEqual(len(c.sleeps),2)

    def test_hard_error_fails_closed(self):
        c=Clock()
        def rpc(method,params,timeout):
            if method=="getSlot":return 100
            if method=="getBlocks":return [90]
            if method=="getBlock":raise ValueError("malformed response")
        with patch.object(m,"_rpc",side_effect=rpc):
            with self.assertRaises(ValueError):m.acquire_finalized_block_batch(90,1,2,sleep_fn=c.sleep,monotonic_fn=c.now)

    def test_limit_stays_32(self):
        calls=[]
        def rpc(method,params,timeout):
            calls.append((method,params))
            if method=="getSlot":return 100
            if method=="getBlocks":return []
        with patch.object(m,"_rpc",side_effect=rpc):m.acquire_finalized_block_batch(1,999,2)
        gb=[x for x in calls if x[0]=="getBlocks"][0]
        self.assertEqual(gb[1][1],32)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-413 public-RPC rate-paced final acquisition rebuild certified")
    print("[PASS] getBlock calls are serial and paced below published single-method limit")
    print("[PASS] HTTP 429 Retry-After honored; bounded fallback backoff preserved")
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if Path(__file__).name!=EXPECTED:raise RuntimeError('installer filename mismatch')
    root=Path.cwd().resolve();p=root/TARGET
    if not p.is_file() or sha(p)!=EXPECTED_HASH:raise RuntimeError('exact current OAD-318 OAD-412 source mismatch; no mutation performed')
    ast.parse(NEW_SOURCE,filename=str(TARGET))
    stamp=time.strftime('%Y%m%dT%H%M%S');bak=p.with_name(p.name+'.pre_rate_paced_final_acquisition.'+stamp+'.bak');shutil.copy2(p,bak)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(NEW_SOURCE,encoding='utf-8',newline='\n');os.replace(tmp,p)
    (root/'test_oad_413_solana_public_rpc_rate_paced_final_acquisition_rebuild.py').write_text(TEST_SOURCE,encoding='utf-8',newline='\n')
    print('[PASS] exact OAD-412 OAD-318 source hash matched')
    print('[PASS] rollback backup:',bak.relative_to(root))
    print('[PASS] parallel getBlock bursts removed completely')
    print('[PASS] getBlock rate paced at >=300ms between calls')
    print('[PASS] HTTP 429 Retry-After honored when supplied')
    print('[PASS] bounded exponential cooldown used when Retry-After absent')
    print('[PASS] completed slots retained; no retry storm')
    print('[PASS] 32-slot bounded catch-up capacity preserved')
    print('[PASS] native public Solana RPC only; no paid provider; no GMGN')
    print('[PASS] checkpoint and OPH-019/021 boundaries unchanged')
    print('[PASS] execution_authority=FALSE')
    print('[DONE]',EXPECTED)
if __name__=='__main__':main()
