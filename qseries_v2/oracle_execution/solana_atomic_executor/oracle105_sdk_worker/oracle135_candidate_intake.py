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
                    with OUT.open('a',encoding='utf8') as g:g.write(json.dumps(rec,sort_keys=True)+'\n')
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
