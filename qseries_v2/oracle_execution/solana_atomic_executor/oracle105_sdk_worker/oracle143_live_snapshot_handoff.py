"""In-memory fresh positive-quote handoff; transaction execution remains disabled."""
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
