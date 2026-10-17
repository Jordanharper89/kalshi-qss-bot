"""ORACLE-135 complete installer: protect warm scanning and validate candidate intake.
No private keys; never constructs, signs, or broadcasts transactions.
"""
from __future__ import annotations
import ast, os, shutil, tempfile, textwrap
from pathlib import Path
ROOT=Path.cwd()
PKG=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
SUP=PKG/'run_oracle126.py'
REPL=PKG/'oracle129_replenish.py'
Q20=ROOT/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
NATIVE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
WORKER=PKG/'oracle135_candidate_intake.py'

CODE=textwrap.dedent('''\
"""Read-only positive quote intake. NOT a transaction simulator or order sender."""
from __future__ import annotations
import argparse, json, os, time
from pathlib import Path
IN=Path('runtime_state/oracle/oracle_live_execution/ORACLE_129_POSITIVE_CANDIDATES.jsonl')
OUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_135_CANDIDATE_INTAKE.jsonl')
STAT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_135_CANDIDATE_STATUS.json')
SIZE=0.050

def classify(row, now=None):
    now=time.time() if now is None else now
    if not isinstance(row,dict):return 'HOLD_INVALID_OBJECT'
    if any(k not in row for k in ('token','pump_pool','meteora_pool','direction','slot','size_sol','captured_unix','quoted_local_net_lamports')):return 'HOLD_INCOMPLETE_IDENTITY'
    if not all(isinstance(row[k],str) and len(row[k])>=30 for k in ('token','pump_pool','meteora_pool')):return 'HOLD_INVALID_POOL_IDENTITY'
    if row['direction'] not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):return 'HOLD_INVALID_DIRECTION'
    try:
        if abs(float(row['size_sol'])-SIZE)>1e-9:return 'HOLD_SIZE_NOT_0050'
        if int(row['quoted_local_net_lamports'])<=0:return 'HOLD_NOT_POSITIVE'
        if int(row['slot'])<=0:return 'HOLD_SLOT'
        age=now-float(row['captured_unix'])
        if age<-.5 or age>1.5:return 'HOLD_STALE_JOURNAL_CANDIDATE'
    except (ValueError,TypeError,OverflowError):return 'HOLD_INVALID_NUMERIC'
    return 'ELIGIBLE_FOR_FRESH_NATIVE_REVALIDATION_ONLY'

def tests():
    a={'token':'a'*40,'pump_pool':'b'*40,'meteora_pool':'c'*40,'direction':'PUMP_TO_METEORA','slot':7,'size_sol':.05,'captured_unix':100.,'quoted_local_net_lamports':1}
    assert classify(a,100.5).startswith('ELIGIBLE_')
    assert classify(dict(a,size_sol=.01),100.5)=='HOLD_SIZE_NOT_0050'
    assert classify(dict(a,captured_unix=90.),100.)=='HOLD_STALE_JOURNAL_CANDIDATE'
    assert classify(dict(a,quoted_local_net_lamports=-1),100.)=='HOLD_NOT_POSITIVE'
    assert classify(dict(a,direction='INVALID'),100.)=='HOLD_INVALID_DIRECTION'
    print('[TEST PASS] ORACLE-135 candidate identity, size, freshness, profit sign, both directions')

def run(seconds=60):
    seen=set();stats={'seen':0,'fresh_for_revalidation':0,'held':0,'no_native_transactions_sent':True}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();position=IN.stat().st_size if IN.exists() else 0
    while time.monotonic()-started<seconds:
        if IN.exists():
            with IN.open('r',encoding='utf8') as f:
                if f.seek(0,2)<position:position=0
                f.seek(position)
                while True:
                    line=f.readline()
                    if not line:break
                    try:row=json.loads(line)
                    except (ValueError,TypeError):row={}
                    key=(str(row.get('token')),str(row.get('direction')),str(row.get('slot')),str(row.get('quoted_local_net_lamports')))
                    if key in seen:continue
                    seen.add(key)
                    decision=classify(row);stats['seen']+=1
                    stats['fresh_for_revalidation' if decision.startswith('ELIGIBLE') else 'held']+=1
                    rec={'decision':decision,'token':str(row.get('token','')),'slot':row.get('slot'), 'size_sol':row.get('size_sol'),'direction':row.get('direction'), 'observed_unix':time.time(),'atomic_simulation_completed':False,'broadcast':False}
                    with OUT.open('a',encoding='utf8') as g:g.write(json.dumps(rec,sort_keys=True)+'\\n')
                    if decision.startswith('ELIGIBLE'):print('[ORACLE135_NATIVE_VALIDATION_REQUIRED] token=%s slot=%s dir=%s size=0.050'% (str(row['token'])[:12],row['slot'],row['direction']),flush=True)
                position=f.tell()
        tmp=STAT.with_suffix('.tmp');tmp.write_text(json.dumps(stats,indent=2),encoding='utf8');os.replace(tmp,STAT)
        time.sleep(.1)
    print('[ORACLE135_INTAKE] '+json.dumps(stats,sort_keys=True),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--seconds',type=float,default=60);a=p.parse_args()
    tests()
    if not a.test:run(a.seconds)
if __name__=='__main__':main()
''')

def patch_supervisor(s):
    old="ap.add_argument('--seconds',type=int,default=300)"
    new="ap.add_argument('--seconds',type=int,default=3600)"
    if old in s:
        if s.count(old)!=1:raise RuntimeError('HOLD_AMBIGUOUS_SESSION')
        s=s.replace(old,new)
    elif new not in s:raise RuntimeError('HOLD_UNKNOWN_SESSION_SEAM')
    start="helper=launch([sys.executable, str(ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py')],env)"
    delayed="helper=launch([sys.executable, str(ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py'),'--delay','45'],env)"
    if start in s:
        if s.count(start)!=1:raise RuntimeError('HOLD_AMBIGUOUS_HELPER_LAUNCH')
        s=s.replace(start,delayed)
    elif delayed not in s:raise RuntimeError('HOLD_UNKNOWN_HELPER_LAUNCH')
    return s

def patch_replenisher(s):
    before="p.add_argument('--once',action='store_true');a=p.parse_args()"
    after="p.add_argument('--once',action='store_true');p.add_argument('--delay',type=float,default=0.0);a=p.parse_args()\n    if a.delay < 0 or a.delay > 120:raise SystemExit('[HOLD] invalid startup delay')\n    if a.delay:print('[ORACLE135_RPC_ISOLATION] warm_start_delay_s=%.0f'%a.delay,flush=True);time.sleep(a.delay)"
    if before in s:
        if s.count(before)!=1:raise RuntimeError('HOLD_AMBIGUOUS_HELPER_ARGS')
        s=s.replace(before,after)
    elif after not in s:raise RuntimeError('HOLD_UNKNOWN_HELPER_ARGS')
    return s

def check(s,r,q,n,w):
    for x in (s,r,q,n,w):ast.parse(x)
    if "default=3600" not in s or "'--delay','45'" not in s:raise RuntimeError('HOLD_SUPERVISOR')
    if "p.add_argument('--delay',type=float,default=0.0)" not in r or 'time.sleep(max(0,180-' not in r:raise RuntimeError('HOLD_REPLENISH')
    def vals(src):
        d={}
        for a in ast.parse(src).body:
            if isinstance(a,ast.Assign):
                for t in a.targets:
                    if isinstance(t,ast.Name) and t.id in ('FAST_SIZES','EXPAND_SIZES','EXECUTION_AUTHORITY','PAPER_ONLY'):
                        d[t.id]=ast.literal_eval(a.value)
        return d
    for src in (q,n):
        v=vals(src)
        if v.get('FAST_SIZES')!=(.05,) or v.get('EXPAND_SIZES')!=() or v.get('EXECUTION_AUTHORITY') is not False or v.get('PAPER_ONLY') is not True:raise RuntimeError('HOLD_UNSAFE_SIZE_OR_AUTHORITY')
    if '_o129_offer(token,snap,slot,received_ns,best)' not in q or "if abs(row['size_sol'] - 0.050) > 1e-10:" not in q:raise RuntimeError('HOLD_CANDIDATE_JOURNAL_MISSING')
    if 'no_native_transactions_sent' not in w:raise RuntimeError('HOLD_INTAKE_GUARD')

def atomic(path,content):
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,prefix='.oracle135_',suffix='.tmp',delete=False) as f:
        f.write(content);p=Path(f.name)
    try:os.replace(p,path)
    finally:p.unlink(missing_ok=True)

def tests():
    sup="ap.add_argument('--seconds',type=int,default=300)\nhelper=launch([sys.executable, str(ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py')],env)\n"
    assert patch_supervisor(patch_supervisor(sup))==patch_supervisor(sup)
    helper="def main():\n    p.add_argument('--once',action='store_true');a=p.parse_args()\n    time.sleep(max(0,180-(time.monotonic()-start)))\n"
    assert patch_replenisher(patch_replenisher(helper))==patch_replenisher(helper)
    ast.parse(CODE)
    print('[TEST PASS] ORACLE-135 stable session, startup RPC separation, 180s cadence, idempotence')

def main():
    tests()
    for p in (SUP,REPL,Q20,NATIVE):
        if not p.is_file():raise SystemExit('[HOLD] Missing prerequisite: '+str(p))
    originals={p:p.read_text(encoding='utf8') for p in (SUP,REPL,Q20,NATIVE)}
    old_worker=WORKER.read_text(encoding='utf8') if WORKER.exists() else None
    updates={SUP:patch_supervisor(originals[SUP]),REPL:patch_replenisher(originals[REPL]),WORKER:CODE}
    check(updates[SUP],updates[REPL],originals[Q20],originals[NATIVE],CODE)
    old={SUP:originals[SUP],REPL:originals[REPL],WORKER:old_worker}
    changed=[]
    for p,new in updates.items():
        if old[p] is not None and old[p]!=new:
            b=p.with_name(p.name+'.oracle135.bak')
            if not b.exists():shutil.copy2(p,b)
    try:
        for p,new in updates.items():
            if old[p]!=new:atomic(p,new);changed.append(p)
        check(SUP.read_text(encoding='utf8'),REPL.read_text(encoding='utf8'),Q20.read_text(encoding='utf8'),NATIVE.read_text(encoding='utf8'),WORKER.read_text(encoding='utf8'))
    except BaseException:
        for p in changed[::-1]:
            if old[p] is None:p.unlink(missing_ok=True)
            else:atomic(p,old[p])
        raise
    print('[INSTALL PASS] ORACLE-135 verified actual repository files')
    print('[SCANNER] stable 3600s sessions reduce repeated full hydration; WebSocket pricing unchanged')
    print('[RPC] independent 180s discovery begins 45s after fast startup')
    print('[SIZE] 0.050 SOL only; both directions preserved')
    print('[INTAKE] local journal freshness and identity verifier installed; NO atomic simulation or live trade authority')
    print('[NEXT] python -m qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle135_candidate_intake --test')
    print('[RUN] python oracle120_credentials.py --run')
if __name__=='__main__':main()
