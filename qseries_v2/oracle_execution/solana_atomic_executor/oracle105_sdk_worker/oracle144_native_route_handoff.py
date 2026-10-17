"""Bounded positive-snapshot native route preflight. Never signs or broadcasts."""
import argparse, collections, json, math, os, queue, threading, time
from pathlib import Path
SIZE=.050
MAX_AGE_NS=750_000_000
Q=queue.Queue(maxsize=64)
COUNTS=collections.Counter()
LOCK=threading.Lock()
STARTED=False
OUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_144_NATIVE_ROUTE_HANDOFF.jsonl')

def admission(token,snap,slot,ns,quote,now=None):
    now=time.perf_counter_ns() if now is None else now
    if not isinstance(snap,dict) or not isinstance(quote,dict) or not isinstance(token,str):return 'HOLD_STRUCTURE'
    try:
        size=float(quote['size_sol']);net=int(quote['local_net']);bps=float(quote['local_bps'])
        direction=str(quote['direction']);slot=int(slot);age=now-int(ns)
    except (ValueError,KeyError,TypeError,OverflowError):return 'HOLD_FIELDS'
    if age<0 or age>MAX_AGE_NS:return 'HOLD_STALE'
    if slot<=0 or not math.isfinite(size) or abs(size-SIZE)>1e-9:return 'HOLD_SIZE'
    if not math.isfinite(bps) or net<=0 or bps<=0:return 'HOLD_NONPOSITIVE'
    if direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):return 'HOLD_DIRECTION_UNKNOWN'
    if not token or snap.get('token')!=token or not snap.get('pump_pool') or not isinstance(snap.get('meteora'),dict):return 'HOLD_PAIR_BINDING'
    if direction!='PUMP_TO_METEORA':return 'HOLD_REVERSE_NATIVE_NOT_CERTIFIED'
    return 'READY_FOR_NATIVE_ROUTE_PROBE'

def offer(token,snap,slot,received_ns,quote):
    decision=admission(token,snap,slot,received_ns,quote)
    with LOCK:COUNTS[decision]+=1
    if decision!='READY_FOR_NATIVE_ROUTE_PROBE':
        _enqueue((token,snap,slot,received_ns,quote,decision))
        return decision
    _enqueue((token,snap,slot,received_ns,quote,decision))
    return decision

def _enqueue(item):
    try:Q.put_nowait(item)
    except queue.Full:
        with LOCK:COUNTS['HOLD_QUEUE_FULL']+=1

def probe_native(token,snap,quote,native=None):
    # No RPC requests or signer calls here. Native template missing means HOLD.
    if native is None:
        from qseries_v2.oracle_execution.solana_atomic_executor import runtime as native
    if not callable(getattr(native,'same_snapshot_route',None)):
        return 'HOLD_NATIVE_ROUTE_API_MISSING',None
    template=getattr(native,'TEMPLATES',{}).get(token)
    if not template:return 'HOLD_NATIVE_TEMPLATE_NOT_INITIALIZED',None
    if template.get('pump_pool')!=snap.get('pump_pool'):
        return 'HOLD_NATIVE_TEMPLATE_DRIFT',None
    # Requires full exact quote fields; never fabricates execution bounds.
    for k in ('start','pump_base_out_gross','pump_base_out_net','pump_max_quote'):
        if k not in quote:return 'HOLD_NATIVE_EXACT_BOUND_MISSING_'+k.upper(),None
    # Routes may include instruction objects; do not serialize or persist those.
    # Avoid signing or simulation; route builder uses existing warm templates.
    try:
        route=native.same_snapshot_route('11111111111111111111111111111111',snap,quote)
    except Exception as e:
        return 'HOLD_NATIVE_ROUTE_'+type(e).__name__,None
    return ('NATIVE_ROUTE_CONSTRUCTED_UNSIMULATED' if route is not None else 'HOLD_EMPTY_NATIVE_ROUTE'),None

def _work():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    while True:
        token,snap,slot,ns,q,decision=Q.get()
        if decision=='READY_FOR_NATIVE_ROUTE_PROBE':
            if time.perf_counter_ns()-int(ns)>MAX_AGE_NS:
                decision='HOLD_EXPIRED_IN_QUEUE'
            else:
                decision,_=probe_native(token,snap,q)
        with LOCK:COUNTS[decision]+=1
        entry={'build':'ORACLE144','token_prefix':str(token)[:12],'slot':slot,'direction':q.get('direction'),
          'size_sol':q.get('size_sol'),'local_bps':q.get('local_bps'),
          'quoted_net_lamports':q.get('local_net'),'decision':decision,
          'signed':False,'simulated':False,'broadcast':False}
        try:
            with OUT.open('a',encoding='utf8') as f:f.write(json.dumps(entry,default=str)+'\n')
        except OSError:
            with LOCK:COUNTS['HOLD_OUTPUT_WRITE']+=1
        Q.task_done()

def start():
    global STARTED
    with LOCK:
        if STARTED:return
        STARTED=True
    threading.Thread(target=_work,daemon=True,name='oracle144-native-route-handoff').start()
    print('[ORACLE144] in-process positive -> bounded native route preflight; no signing, no broadcast',flush=True)

def test():
    now=1_000_000_000
    snap={'token':'T','pump_pool':'P','meteora':{'address':'M'}}
    q={'size_sol':.050,'local_net':90000,'local_bps':18.,'direction':'PUMP_TO_METEORA'}
    assert admission('T',snap,44,now-1_000_000,q,now)=='READY_FOR_NATIVE_ROUTE_PROBE'
    assert admission('T',snap,44,now-1_000_000,dict(q,direction='METEORA_TO_PUMP'),now)=='HOLD_REVERSE_NATIVE_NOT_CERTIFIED'
    assert admission('T',snap,44,now-800_000_000,q,now)=='HOLD_STALE'
    assert admission('T',snap,44,now-1_000_000,dict(q,local_net=-1),now)=='HOLD_NONPOSITIVE'
    assert admission('T',snap,44,now-1_000_000,dict(q,size_sol=.1),now)=='HOLD_SIZE'
    class Native:
        TEMPLATES={'T':{'pump_pool':'P'}}
        @staticmethod
        def same_snapshot_route(user,snap,q):return {'instructions':[1]}
    assert probe_native('T',snap,q,Native)[0].startswith('HOLD_NATIVE_EXACT_BOUND_MISSING')
    assert probe_native('T',snap,dict(q,start=1,pump_base_out_gross=1,pump_base_out_net=1,pump_max_quote=1),Native)[0]=='NATIVE_ROUTE_CONSTRUCTED_UNSIMULATED'
    print('[TEST PASS] ORACLE144 native route probe; freshness, identity, reverse HOLD, size=0.050, no signing/broadcast')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');a=ap.parse_args()
    if a.test:test();return 0
    test();print('[MODE] ORACLE144 is embedded in Q20; launch existing oracle120_credentials.py --run');return 0
if __name__=='__main__':raise SystemExit(main())
