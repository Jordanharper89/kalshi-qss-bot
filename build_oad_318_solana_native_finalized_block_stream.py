from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-318'; TITLE='SOLANA NATIVE FINALIZED BLOCK STREAM'; EXPECTED='build_oad_318_solana_native_finalized_block_stream.py'; MODULE='oad_318_solana_native_finalized_block_stream.py'; TEST='test_oad_318_solana_native_finalized_block_stream.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_148_solana_mainnet_chain_state_acquisition.py': ('def _rpc', 'getSlot'), 'qseries_v2/oracle_adapters/independent/oad_149_solana_finalized_block_activity_acquisition.py': ('getBlock', 'finalized')}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_148_solana_mainnet_chain_state_acquisition import _rpc
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaFinalizedBlockBatch:
    head_slot:int; requested_start:int; finalized_slots:tuple; blocks:tuple; transaction_count:int; execution_authority:bool=False
def acquire_finalized_block_batch(start_slot=None,limit=4,timeout_seconds=20.0):
    head=int(_rpc("getSlot",[{"commitment":"finalized"}],timeout_seconds))
    limit=max(1,min(int(limit),32))
    start=max(0,int(start_slot) if start_slot is not None else head-limit+1)
    slots=tuple(int(x) for x in (_rpc("getBlocks",[start,head,{"commitment":"finalized"}],timeout_seconds) or ()))
    slots=slots[-limit:]
    blocks=[]; txc=0
    for slot in slots:
        b=_rpc("getBlock",[slot,{"commitment":"finalized","encoding":"jsonParsed","transactionDetails":"full","rewards":False,"maxSupportedTransactionVersion":0}],timeout_seconds)
        if not isinstance(b,dict): continue
        tx=tuple(b.get("transactions") or ()); txc+=len(tx)
        blocks.append((slot,b))
    return SolanaFinalizedBlockBatch(head,start,slots,tuple(blocks),txc,False)

"""
TEST_SOURCE=r"""\

import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_318_solana_native_finalized_block_stream as m
class T(unittest.TestCase):
 def test_batch(self):
  def rpc(method,params,timeout):
   if method=="getSlot": return 102
   if method=="getBlocks": return [100,101,102]
   if method=="getBlock": return {"blockhash":"h"+str(params[0]),"transactions":[{"transaction":{"signatures":["s"]}}]}
  with patch.object(m,"_rpc",side_effect=rpc):
   x=m.acquire_finalized_block_batch(100,3)
  print("[BLOCKS]",x.finalized_slots,"transactions=",x.transaction_count)
  self.assertEqual(x.finalized_slots,(100,101,102)); self.assertEqual(x.transaction_count,3)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-318 finalized native Solana block-range acquisition certified")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src: raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("frozen boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("frozen boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] frozen OPH-023/Kalshi OAD-055 unchanged")
        print("[PASS] native Solana RPC foundation; GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
