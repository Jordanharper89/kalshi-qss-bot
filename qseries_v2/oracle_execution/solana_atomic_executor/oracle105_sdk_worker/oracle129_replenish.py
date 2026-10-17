"""ORACLE-129 background auxiliary replenisher: startup + 180 s cadence."""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path.cwd()
MODULES=[
 'qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_045b_evidence_window_hotset_lifecycle',
 'qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_071_continuous_mriya_replenishment',
]
DISCOVERY='from pathlib import Path\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.crosslisted import crosslisted\nimport json,os,time\npump,pairs=crosslisted(Path.cwd(),capture_seconds=5,max_intersections=56)\nrows=[]\nfor p in pairs:\n    m=p.get("meteora") or {}\n    if p.get("token") and p.get("pump_pool") and m.get("address"):\n        rows.append({"token":p["token"],"pump_pool":p["pump_pool"],"meteora_pool":m["address"],"pump_activity":p.get("pump_activity",0),"observed_unix":time.time()})\nf=Path("runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json")\nf.parent.mkdir(parents=True,exist_ok=True)\nt=f.with_suffix(".tmp")\nt.write_text(json.dumps({"rows":rows,"observed_unix":time.time(),"pump_active_pools":pump.get("active_pools",0)},indent=2),encoding="utf-8")\nos.replace(t,f)\nprint("[UNIVERSAL] active_pump_pools=%d crosslisted=%d"%(pump.get("active_pools",0),len(rows)),flush=True)\n'
REPORT=ROOT/'runtime_state/oracle/oracle_live_execution/ORACLE_129_REPLENISH.json'
def clean_env():
    e=os.environ.copy()
    for k in list(e):
        if any(s in k.upper() for s in ('PRIVATE_KEY','SECRET_KEY','MNEMONIC','SEED_PHRASE')):
            del e[k]
    e['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    return e

def cycle():
    env=clean_env(); records=[]
    for cmd in [[sys.executable,'-m',m] for m in MODULES]+[[sys.executable,'-c',DISCOVERY]]:
        name=cmd[2] if cmd[1]=='-m' else 'universal_crosslist'
        try:
            # Cap subprocess cost; timeout is reported and not counted as success.
            p=subprocess.run(cmd,cwd=ROOT,env=env,timeout=25,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            lines=p.stdout.splitlines()
            for s in lines[-5:]:
                if s.startswith(('[UNIVERSAL]','[REPLENISH]','[MRIYA_HOTSET]','[LIFECYCLE_COUNTS]','[WARM_SKIP]')):
                    print(s,flush=True)
            result={'job':name,'returncode':p.returncode,'seconds_limit':25,'rate_limited':any('429' in s for s in lines)}
        except subprocess.TimeoutExpired:
            result={'job':name,'returncode':None,'timeout':True}
        except Exception as ex:
            result={'job':name,'error':type(ex).__name__}
        records.append(result)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    tmp=REPORT.with_suffix('.tmp')
    tmp.write_text(json.dumps({'revision':'ORACLE-129','completed_unix':time.time(),'jobs':records,'pricing_lane_separate':True,'live_hot_cutover_certified':False},indent=2),encoding='utf8')
    os.replace(tmp,REPORT)
    print('[REPLENISH_129] jobs=%s'%[(x['job'].split('.')[-1],x.get('returncode')) for x in records],flush=True)
    return records

def main():
    p=argparse.ArgumentParser();p.add_argument('--once',action='store_true');p.add_argument('--delay',type=float,default=0.0);a=p.parse_args()
    if a.delay < 0 or a.delay > 120:raise SystemExit('[HOLD] invalid startup delay')
    if a.delay:print('[ORACLE135_RPC_ISOLATION] warm_start_delay_s=%.0f'%a.delay,flush=True);time.sleep(a.delay)
    while True:
        start=time.monotonic()
        cycle()
        if a.once:return 0
        # 180 s target between starts; slow cycles cannot overlap.
        time.sleep(max(0,180-(time.monotonic()-start)))
if __name__=='__main__':raise SystemExit(main())
