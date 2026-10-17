"""ORACLE-143 full installer: in-process positive snapshot handoff, fail-closed native boundary."""
from pathlib import Path
import ast, os, subprocess, sys, tempfile

ROOT=Path.cwd()
FAST=ROOT/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
NATIVE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
PKG=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
TARGET=PKG/'oracle143_live_snapshot_handoff.py'
MODULE=r'''"""In-memory fresh positive-quote handoff; transaction execution remains disabled."""
import argparse, collections, json, math, queue, threading, time
from pathlib import Path
Q=queue.Queue(maxsize=128)
COUNTS=collections.Counter()
STARTED=False
LOCK=threading.Lock()
OUTPUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_143_SNAPSHOT_HANDOFF.jsonl')
SIZE=.050
MAX_AGE_NS=750_000_000
RESERVE=125_000  # 25 bps on 0.050 SOL; screening assumption, NOT actual costs.

def evaluate(token,snap,slot,received_ns,quote,now_ns=None):
    now_ns=time.perf_counter_ns() if now_ns is None else now_ns
    if not isinstance(snap,dict) or not isinstance(quote,dict):return 'HOLD_STRUCTURE'
    if not isinstance(token,str) or not token:return 'HOLD_TOKEN'
    try:
        age=now_ns-int(received_ns)
        net=int(quote['local_net']); size=float(quote['size_sol']);bps=float(quote['local_bps'])
        direction=str(quote['direction']);slot=int(slot)
    except (KeyError,ValueError,TypeError,OverflowError):return 'HOLD_QUOTE_FIELDS'
    if age<0 or age>MAX_AGE_NS:return 'HOLD_STALE'
    if slot<=0 or not math.isfinite(size) or abs(size-SIZE)>1e-9:return 'HOLD_SIZE_OR_SLOT'
    if not math.isfinite(bps) or net<=0 or bps<=0:return 'HOLD_NONPOSITIVE'
    if direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):return 'HOLD_DIRECTION'
    if not snap.get('pump_pool') or not isinstance(snap.get('meteora'),dict):return 'HOLD_POOL_STATE'
    if net<=RESERVE:return 'HOLD_BELOW_SCREENING_RESERVE'
    # Snapshot stays in this process; current native compiler context not initialized here.
    return 'HOLD_NATIVE_CONTEXT_UNINITIALIZED'

def offer(token,snap,slot,received_ns,quote):
    decision=evaluate(token,snap,slot,received_ns,quote)
    with LOCK: COUNTS[decision]+=1
    try:
        Q.put_nowait((token,snap,int(slot),int(received_ns),dict(quote),decision))
    except queue.Full:
        with LOCK: COUNTS['HOLD_QUEUE_FULL']+=1
    return decision

def _writer():
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    while True:
        token,snap,slot,received_ns,quote,decision=Q.get()
        record={'revision':'ORACLE-143','token_prefix':token[:12],'slot':slot,
            'direction':quote.get('direction'),'size_sol':quote.get('size_sol'),
            'quoted_bps':quote.get('local_bps'),'quoted_net_lamports':quote.get('local_net'),
            'age_at_write_ms':round((time.perf_counter_ns()-received_ns)/1e6,2),
            'decision':decision,'native_simulated':False,'broadcast':False,
            'reason':'Native compiler must be initialized with CURRENT snapshot before safe signed simulation.'}
        try:
            with OUTPUT.open('a',encoding='utf8') as f:f.write(json.dumps(record,default=str)+'\n')
        except OSError:
            with LOCK:COUNTS['HOLD_OUTPUT_IO']+=1
        Q.task_done()

def start():
    global STARTED
    with LOCK:
        if STARTED:return
        STARTED=True
    threading.Thread(target=_writer,daemon=True,name='oracle143-snapshot-journal').start()
    print('[ORACLE143] IN_PROCESS_SNAPSHOT_HANDOFF size=0.050 native_simulation=HOLD broadcast=FALSE',flush=True)

def test():
    now=1_000_000_000
    snap={'pump_pool':'pool','meteora':{'address':'dlmm'}}
    q={'local_net':125001,'local_bps':26.,'size_sol':.05,'direction':'PUMP_TO_METEORA'}
    assert evaluate('token',snap,1,now-10_000_000,q,now)=='HOLD_NATIVE_CONTEXT_UNINITIALIZED'
    assert evaluate('token',snap,1,now-10_000_000,dict(q,direction='METEORA_TO_PUMP'),now)=='HOLD_NATIVE_CONTEXT_UNINITIALIZED'
    assert evaluate('token',snap,1,now-800_000_000,q,now)=='HOLD_STALE'
    assert evaluate('token',snap,1,now-10_000_000,dict(q,local_net=100),now)=='HOLD_BELOW_SCREENING_RESERVE'
    assert evaluate('token',snap,1,now-10_000_000,dict(q,size_sol=.1),now)=='HOLD_SIZE_OR_SLOT'
    print('[TEST PASS] ORACLE143 positive snapshot, both routes, stale/margin holds, no execution',flush=True)

if __name__=='__main__':
    test()
'''

def main():
    for p in (FAST,NATIVE):
        if not p.is_file():raise SystemExit('[HOLD] Missing canonical source '+str(p))
    src=FAST.read_text(encoding='utf8'); native=NATIVE.read_text(encoding='utf8')
    for v in (src,native,MODULE):ast.parse(v)
    if 'EXECUTION_AUTHORITY=False' not in native and 'EXECUTION_AUTHORITY = False' not in native:
        raise SystemExit('[HOLD] Native no-execution guard missing')
    if '_o129_offer(' not in src:
        raise SystemExit('[HOLD] Positive-source injection absent; scanner unchanged')
    # Inject after exact scan is complete, where the positive-quote path already exists.
    anchor='self.positive+=1'
    if src.count(anchor)!=1:raise SystemExit('[HOLD] Q20 positive hook count mismatch')
    marker='_o143.offer(token,snap,slot,received_ns,best)'
    if marker not in src:
        block=("\n            from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle143_live_snapshot_handoff as _o143\n"
               "            _o143.start()\n"
               "            _o143.offer(token,snap,slot,received_ns,best)\n")
        # Preserves existing indentation of the original positive branch.
        src=src.replace(anchor,anchor+block,1)
    ast.parse(src)
    PKG.mkdir(parents=True,exist_ok=True)
    old_fast=FAST.read_bytes(); old_mod=TARGET.read_bytes() if TARGET.exists() else None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=PKG,delete=False) as t:
            t.write(MODULE);tmp=Path(t.name)
        os.replace(tmp,TARGET)
        with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=FAST.parent,delete=False) as t:
            t.write(src);tmp=Path(t.name)
        os.replace(tmp,FAST)
        p=subprocess.run([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle143_live_snapshot_handoff'],capture_output=True,text=True,timeout=20,cwd=ROOT)
        if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-2000:])
        print(p.stdout.strip())
    except BaseException as e:
        FAST.write_bytes(old_fast)
        if old_mod is None:TARGET.unlink(missing_ok=True)
        else:TARGET.write_bytes(old_mod)
        raise SystemExit('[HOLD] ORACLE143 rolled back: '+str(e))
    print('[INSTALL PASS] ORACLE143 in-process positive snapshot capture; native execution still HELD')
    print('[RUN] python oracle120_credentials.py --run')
if __name__=='__main__':main()
