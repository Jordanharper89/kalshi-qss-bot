"""ORACLE-142. Read-only profit gate; no transaction construction or broadcasting."""
from __future__ import annotations
import argparse, collections, json, math, os, time
from pathlib import Path
SRC=Path('runtime_state/oracle/oracle_live_execution/ORACLE_129_POSITIVE_CANDIDATES.jsonl')
DEST=Path('runtime_state/oracle/oracle_live_execution/ORACLE_142_PROFIT_ADMISSION.jsonl')
STATUS=Path('runtime_state/oracle/oracle_live_execution/ORACLE_142_PROFIT_STATUS.json')
SIZE=0.050
FRESH_S=0.750
# Explicit minimum economic reserve above reported quote PnL. Not a substitute for fee estimation/simulation.
RESERVE_BPS=25.0
RESERVE_LAMPORTS=round(SIZE*1_000_000_000*RESERVE_BPS/10_000)
REQUIRED=('token','pump_pool','meteora_pool','slot','direction','size_sol','captured_unix','quoted_local_net_lamports','quoted_local_bps')

def validate(row,now=None):
    now=time.time() if now is None else now
    if not isinstance(row,dict) or any(k not in row for k in REQUIRED):return 'HOLD_INCOMPLETE',None
    if not all(isinstance(row[k],str) and 32<=len(row[k])<=64 for k in ('token','pump_pool','meteora_pool')):return 'HOLD_IDENTITY',None
    if row['direction'] not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):return 'HOLD_DIRECTION',None
    try:
        size=float(row['size_sol']); age=now-float(row['captured_unix']); slot=int(row['slot'])
        net=int(row['quoted_local_net_lamports']); bps=float(row['quoted_local_bps'])
        if not all(math.isfinite(x) for x in (size,age,bps)):return 'HOLD_NONFINITE',None
    except (ValueError,TypeError,OverflowError):return 'HOLD_NUMERIC',None
    if abs(size-SIZE)>1e-9:return 'HOLD_SIZE',None
    if slot<=0:return 'HOLD_SLOT',None
    if age < -0.5 or age > FRESH_S:return 'HOLD_STALE',None
    if net<=0 or bps<=0:return 'HOLD_NOT_POSITIVE',None
    if net<=RESERVE_LAMPORTS:return 'HOLD_MARGIN_BELOW_RESERVE',None
    return 'PASS_PRELIMINARY_ONLY',{'age_ms':round(age*1000,1),'quoted_surplus_lamports':net-RESERVE_LAMPORTS}

def test():
    x=dict(token='1'*40,pump_pool='2'*40,meteora_pool='3'*40,slot=42,direction='PUMP_TO_METEORA',size_sol=.05,captured_unix=100,quoted_local_net_lamports=RESERVE_LAMPORTS+1,quoted_local_bps=50.0)
    assert validate(x,100.2)[0]=='PASS_PRELIMINARY_ONLY'
    assert validate(dict(x,direction='METEORA_TO_PUMP'),100.2)[0]=='PASS_PRELIMINARY_ONLY'
    assert validate(dict(x,size_sol=.01),100.2)[0]=='HOLD_SIZE'
    assert validate(dict(x,captured_unix=98),100.2)[0]=='HOLD_STALE'
    assert validate(dict(x,quoted_local_net_lamports=RESERVE_LAMPORTS),100.2)[0]=='HOLD_MARGIN_BELOW_RESERVE'
    assert validate(dict(x,quoted_local_bps=-1),100.2)[0]=='HOLD_NOT_POSITIVE'
    assert validate(dict(x,quoted_local_bps=float('nan')),100.2)[0]=='HOLD_NONFINITE'
    assert validate(dict(x,slot=0),100.2)[0]=='HOLD_SLOT'
    print('[TEST PASS] ORACLE142 both_directions size=0.050 freshness=750ms margin=25bps no_sign_no_broadcast',flush=True)

def write_status(stats):
    STATUS.parent.mkdir(parents=True,exist_ok=True)
    payload={'revision':'ORACLE-142','updated_unix':time.time(),'counts':dict(stats),'minimum_reserve_lamports':RESERVE_LAMPORTS,
       'reserve_is_estimate_not_actual_fees':True,'atomic_signed_simulations_passed':0,'broadcast':False,
       'live_execution_certified':False,'next_gate':'NATIVE_REBUILD_AND_SIGNED_SIMULATION_FROM_CURRENT_SNAPSHOT'}
    tmp=STATUS.with_suffix('.tmp');tmp.write_text(json.dumps(payload,indent=2),encoding='utf8');os.replace(tmp,STATUS)

def run(seconds,from_start=False):
    DEST.parent.mkdir(parents=True,exist_ok=True)
    counters=collections.Counter();seen=set();started=time.monotonic()
    position=0 if from_start else SRC.stat().st_size if SRC.exists() else 0
    print('[ORACLE142] PROFIT_ADMISSION size=0.050 reserve=25bps fresh<=750ms simulate=FALSE broadcast=FALSE',flush=True)
    while time.monotonic()-started<seconds:
        if SRC.exists():
            with SRC.open('r',encoding='utf8') as f:
                end=f.seek(0,2)
                if end<position:position=0
                f.seek(position)
                while True:
                    line=f.readline()
                    if not line:break
                    # Do not process partially written JSON lines.
                    if not line.endswith('\n'):break
                    position=f.tell()
                    try:row=json.loads(line)
                    except json.JSONDecodeError:row={}
                    decision,detail=validate(row)
                    k=(str(row.get('token')),str(row.get('direction')),str(row.get('slot')),str(row.get('quoted_local_net_lamports')))
                    if k in seen:continue
                    seen.add(k)
                    if len(seen)>20000:seen.clear()
                    counters[decision]+=1
                    output={'decision':decision,'token':str(row.get('token',''))[:12], 'direction':row.get('direction'),
                        'slot':row.get('slot'),'quoted_local_bps':row.get('quoted_local_bps'),
                        'observed_unix':time.time(),'native_simulated':False,'broadcast':False}
                    if detail:output.update(detail)
                    with DEST.open('a',encoding='utf8') as out:out.write(json.dumps(output,sort_keys=True)+'\n')
                    if decision=='PASS_PRELIMINARY_ONLY':
                        print('[ORACLE142_NATIVE_SIM_REQUIRED] token=%s direction=%s slot=%s quote_surplus=%s'%
                              (output['token'],output['direction'],output['slot'],detail['quoted_surplus_lamports']),flush=True)
        write_status(counters)
        time.sleep(0.1)
    print('[ORACLE142_REPORT] '+json.dumps(dict(counters),sort_keys=True),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--seconds',type=float,default=3600);ap.add_argument('--from-start',action='store_true')
    args=ap.parse_args();test()
    if not args.test:
        if not 1<=args.seconds<=86400:raise SystemExit('HOLD_INVALID_SECONDS')
        run(args.seconds,args.from_start)
if __name__=='__main__':main()
