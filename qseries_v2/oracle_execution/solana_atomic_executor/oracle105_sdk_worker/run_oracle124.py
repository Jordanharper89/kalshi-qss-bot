"""ORACLE-124: original universal PumpSwap/Meteora crosslisting + Mriya activity + lifecycle + SDK evaluator.
No scanner edits, no signing/broadcast. An install/test pass is not profit.
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time,shutil,getpass
from pathlib import Path

ROOT=Path.cwd()
HERE=Path(__file__).resolve().parent
WORKER=HERE/'oracle124_atomic_machine.cjs'
REPO='qseries_v2/oracle_strategy_intelligence/solana_money'
MRIYA='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery'
REPLENISH='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_071_continuous_mriya_replenishment'
LIFECYCLE='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_045b_evidence_window_hotset_lifecycle'
REPL_FILE=ROOT/'runtime_state/qseries/qarb_clean_bot/qarb_071_replenishment.json'
LIFE_FILE=ROOT/'runtime_state/qseries/qarb_clean_bot/mriya_dynamic_hotset_lifecycle.json'
UNIVERSAL_FILE=ROOT/'runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json'
CANONICAL=ROOT/'runtime_state/oracle/oracle_live_execution/ORACLE_122_LIVE_REPLENISHED_PAIRS.json'
STATIC=ROOT/'runtime_state/oracle/solana_atomic_executor'
IDENT=('token','pump_pool','meteora_pool')

def read(p):
    try:
        if p.stat().st_size>20_000_000:return {}
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError,TypeError):return {}
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix('.json.tmp')
    t.write_text(json.dumps(d,sort_keys=True,indent=2),encoding='utf-8')
    os.replace(t,p)
def rows(d):
    return d if isinstance(d,list) else d.get('rows',[]) if isinstance(d,dict) else []
def materialize():
    live=read(UNIVERSAL_FILE)
    rep=read(REPL_FILE)
    life=read(LIFE_FILE)
    registry=rep.get('tokens',{}) if isinstance(rep,dict) else {}
    stages={x['token']:x['stage'] for x in rows(life) if isinstance(x,dict) and x.get('token') and x.get('stage')}
    ranked={}; source_counts={}
    def admit(x,source):
        if not isinstance(x,dict) or any(not isinstance(x.get(k),str) or not x.get(k) for k in IDENT):return
        k=tuple(x[v] for v in IDENT)
        # Promote active pool evidence; retain retired pool identities for later rediscovery.
        rank={'UNIVERSAL_LIVE_CROSSLIST':0,'MRIYA_REPLENISHED':1,'HISTORICAL_IDENTITY_ONLY':2}[source]
        prev=ranked.get(k)
        if prev is None or rank<prev[0]:
            ranked[k]=(rank,dict(x,source=source,lifecycle=stages.get(x['token'],'OBSERVE')))
    # Live independent crosslisting is first priority.
    for x in rows(live):admit(x,'UNIVERSAL_LIVE_CROSSLIST')
    if isinstance(registry,dict):
        for x in registry.values():admit(x,'MRIYA_REPLENISHED')
    for name in ('live_hot_book.json','capacity_aware_warm_universe.json','full_surface_replenishment_inventory.json','multi_dlmm_pair_registry.json'):
        for x in rows(read(STATIC/name)):admit(x,'HISTORICAL_IDENTITY_ONLY')
    values=[v for _,v in sorted(ranked.values(),key=lambda q:(q[0],{'HOT':0,'ACTIVE':1,'COOLING':2,'RECHECK':3,'OBSERVE':4,'RETIRED':5}.get(q[1]['lifecycle'],4),q[1]['token']))]
    for v in values:source_counts[v['source']]=source_counts.get(v['source'],0)+1
    result={'revision':'ORACLE-124','observed_unix':time.time(),'rows':values,
            'source_counts':source_counts,'universal_observed_unix':live.get('observed_unix') if isinstance(live,dict) else None,
            'mriya_registry_tokens':len(registry) if isinstance(registry,dict) else 0,
            'identity_count':len(values),'verified_bidirectional_quotes':0,
            'min_quotable_pairs_target':28,'inventory_is_not_live_profitability_evidence':True,
            'execution_authority':False,'broadcast':False}
    write(CANONICAL,result)
    return result

def universal_capture(env):
    # This uses existing repository code. It never edits or replaces the frozen scanner.
    snippet="""import json,time,os
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.crosslisted import crosslisted
pump,pairs=crosslisted(Path.cwd(),capture_seconds=5,max_intersections=56)
out=[]
for p in pairs:
 m=p.get('meteora') or {}
 if all((p.get('token'),p.get('pump_pool'),m.get('address'))):
  out.append({'token':p['token'],'pump_pool':p['pump_pool'],'meteora_pool':m['address'],'reported_tvl':m.get('score',0),'pump_activity':p.get('pump_activity',0),'observed_unix':time.time()})
file=Path('runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json')
file.parent.mkdir(parents=True,exist_ok=True)
temp=file.with_suffix('.json.tmp');temp.write_text(json.dumps({'rows':out,'observed_unix':time.time(),'pump_active_pools':pump.get('active_pools',0),'active_overlap':pump.get('active_overlap',0)},indent=2),encoding='utf8');os.replace(temp,file)
print('[UNIVERSAL] active_pump_pools=%d crosslisted=%d'%(pump.get('active_pools',0),len(out)),flush=True)
"""
    return subprocess.run([sys.executable,'-c',snippet],env=env,cwd=ROOT,timeout=150,check=False).returncode

def run_module(module,env,timeout=90):
    try:return subprocess.run([sys.executable,'-m',module],cwd=ROOT,env=env,timeout=timeout,check=False).returncode
    except subprocess.TimeoutExpired:return 124

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--watch',action='store_true')
    ap.add_argument('--trade',action='store_true')
    ap.add_argument('--once',action='store_true')
    a=ap.parse_args()
    if a.trade:
        print('[HOLD] LIVE_EXECUTION_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST',flush=True)
        return 2
    needed=[ROOT/('qseries_v2/oracle_strategy_intelligence/solana_money/mriya_python_paper_arb/crosslisted.py'),ROOT/('qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/qarb_043b_paced_mriya_token_discovery.py'),WORKER]
    if not shutil.which('node') or any(not p.is_file() for p in needed):
        print('[HOLD] ORIGINAL_DISCOVERY_OR_SDK_WORKER_MISSING',flush=True);return 2
    env=os.environ.copy()
    if not env.get('SOLANA_RPC_URL','').startswith('https://'):
        key=getpass.getpass('Helius API key (hidden): ').strip()
        if not key:return 2
        env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+key
    env.setdefault('SOLANA_WS_URL',env['SOLANA_RPC_URL'].replace('https://','wss://',1))
    if not env.get('ORACLE_PUBLIC_KEY') and not env.get('QSB_SOLANA_PRIVATE_KEY'):
        print('[HOLD] WALLET_PUBLIC_ADDRESS_REQUIRED_FOR_SDK_SIMULATION',flush=True);return 2
    scanenv={k:v for k,v in env.items() if not any(q in k.upper() for q in ('PRIVATE_KEY','SECRET_KEY','MNEMONIC'))}
    print('[ORACLE-124] UNIVERSAL_PUMP_METEORA + MRIYA_WS + LIFECYCLE + REPLENISHMENT + ATOMIC_SDK_WATCH',flush=True)
    print('[GUARD] EXECUTION_AUTHORITY=FALSE SIGNING=FALSE BROADCAST=FALSE canary=0.010_SOL',flush=True)
    scanner=None;worker=None;last_universal=0;last_life=0
    try:
        scanner=subprocess.Popen([sys.executable,'-m',MRIYA],cwd=ROOT,env=scanenv)
        tick=0
        while True:
            tick+=1
            if scanner.poll() is not None:
                print('[DISCOVERY_RECOVERY] code=%s'%scanner.returncode,flush=True)
                scanner=subprocess.Popen([sys.executable,'-m',MRIYA],cwd=ROOT,env=scanenv)
            now=time.monotonic()
            if now-last_universal>=180 or tick==1:
                last_universal=now
                try:
                    rc=universal_capture(scanenv)
                    if rc:print('[UNIVERSAL_WARNING] capture_exit=%s keep_prior_inventory'%rc,flush=True)
                except Exception as e:print('[UNIVERSAL_WARNING] %s'%type(e).__name__,flush=True)
            if now-last_life>=120 or tick==1:
                last_life=now
                rc=run_module(LIFECYCLE,scanenv)
                if rc:print('[LIFECYCLE_WARNING] exit=%s'%rc,flush=True)
            rc=run_module(REPLENISH,scanenv)
            if rc:print('[REPLENISH_WARNING] exit=%s'%rc,flush=True)
            inv=materialize()
            print('[INVENTORY] identities=%d sources=%s target_bidirectional_quotes=28'% (inv['identity_count'],inv['source_counts']),flush=True)
            if a.once:
                return subprocess.call(['node',str(WORKER),'--watch','--once'],cwd=ROOT,env=env)
            if worker is None or worker.poll() is not None:
                if worker is not None:print('[EVALUATOR_RECOVERY] code=%s'%worker.returncode,flush=True)
                worker=subprocess.Popen(['node',str(WORKER),'--watch'],cwd=ROOT,env=env)
            time.sleep(60)
    except KeyboardInterrupt:
        print('[STOP] ORACLE-124',flush=True);return 0
    finally:
        for process in (worker,scanner):
            if process is not None and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=8)
                except subprocess.TimeoutExpired:process.kill()
if __name__=='__main__':raise SystemExit(main())
