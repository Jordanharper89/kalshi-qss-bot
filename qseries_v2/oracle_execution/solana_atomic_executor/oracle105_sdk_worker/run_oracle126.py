"""ORACLE-126: restored original FAST scanner with independent discovery, watch-only."""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time,threading,queue,traceback
from pathlib import Path

ROOT=Path.cwd()
FAST='qseries_v2.oracle_execution.oracle_025_single_hydration_exact_live_reuse'
MRIYA='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery'
REPLENISH='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_071_continuous_mriya_replenishment'
LIFECYCLE='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_045b_evidence_window_hotset_lifecycle'
NATIVE='qseries_v2.oracle_execution.solana_atomic_executor.runtime'
REPORT=ROOT/'runtime_state/oracle/oracle_live_execution/ORACLE_126_ORIGINAL_FAST_RESTORE.json'
STOP=threading.Event()
SUBPROCS=[]


def sanitized_env():
    env=os.environ.copy()
    for key in list(env):
        if any(x in key.upper() for x in ('PRIVATE_KEY','MNEMONIC','SECRET_KEY','SEED_PHRASE')):
            env.pop(key,None)
    # Never need a signing key for original q25/q20 scanner.
    env['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    env['QSB_PAPER_ONLY']='TRUE'
    return env


def write_report(details):
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    values={'revision':'ORACLE-126','restored_fast_path':FAST,
        'fast_scanner_is_original_repo_code':True,'execution_authority':False,
        'signing_enabled':False,'broadcast_enabled':False,'canary_sol':'0.010',
        'updated_unix':time.time(),**details}
    path=REPORT.with_suffix('.json.tmp')
    path.write_text(json.dumps(values,sort_keys=True,indent=2),encoding='utf8')
    os.replace(path,REPORT)


def launch(args,env):
    p=subprocess.Popen(args,cwd=str(ROOT),env=env)
    SUBPROCS.append(p)
    return p


def discover_loop(env):
    # The old q25 account-event pricing loop is the primary runtime; these are
    # secondary and cannot replace it or cause pricing to wait on hydration.
    code="""import json,os,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.crosslisted import crosslisted
pump,pairs=crosslisted(Path.cwd(),capture_seconds=5,max_intersections=56)
out=[]
for p in pairs:
 m=p.get('meteora') or {}
 if p.get('token') and p.get('pump_pool') and m.get('address'):
  out.append({'token':p['token'],'pump_pool':p['pump_pool'],'meteora_pool':m['address'],
              'observed_unix':time.time(),'pump_activity':p.get('pump_activity',0),'reported_tvl':m.get('score',0)})
fn=Path('runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json')
fn.parent.mkdir(parents=True,exist_ok=True)
tmp=fn.with_suffix('.json.tmp')
tmp.write_text(json.dumps({'rows':out,'observed_unix':time.time(),
    'pump_active_pools':pump.get('active_pools',0)},indent=2),encoding='utf8')
os.replace(tmp,fn)
print('[UNIVERSAL] active_pump_pools=%s crosslisted=%s'%(pump.get('active_pools',0),len(out)),flush=True)
"""
    while not STOP.is_set():
        try:
            # Throttle optional RPC-heavy discovery and never stall fast scanner.
            # Separate scanner is reused unchanged, not replaced.
            for module in (LIFECYCLE,REPLENISH):
                if STOP.is_set():break
                try:
                    p=launch([sys.executable,'-m',module],env)
                    p.wait(timeout=75)
                    print('[AUX]',module.rsplit('.',1)[-1], 'exit='+str(p.returncode),flush=True)
                except subprocess.TimeoutExpired:
                    p.kill();p.wait()
                    print('[AUX_TIMEOUT]',module.rsplit('.',1)[-1],flush=True)
            if not STOP.is_set():
                p=launch([sys.executable,'-c',code],env)
                try:p.wait(timeout=120)
                except subprocess.TimeoutExpired:p.kill();p.wait()
                print('[DISCOVERY_PASS] exit='+str(p.returncode),flush=True)
        except Exception as exc:
            print('[DISCOVERY_HOLD]',type(exc).__name__,flush=True)
        STOP.wait(180)


def verify_executor():
    # Explicitly inspect the existing original atomic runtime without importing
    # or calling its transaction builder (no secret, no wallet, no mutation).
    p=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
    if not p.is_file():return 'MISSING_NATIVE_EXECUTOR'
    import ast
    t=ast.parse(p.read_text(encoding='utf8'))
    flags={}
    for node in t.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in ('EXECUTION_AUTHORITY','PAPER_ONLY','REAL_MONEY_MOVED'):
                    try:flags[target.id]=ast.literal_eval(node.value)
                    except (ValueError,TypeError):flags[target.id]='DYNAMIC'
    print('[EXECUTOR_ATTACHED] module='+str(p)+' flags='+str(flags),flush=True)
    return 'CERTIFICATION_REQUIRED' # existence is not permission to broadcast


def run(once=False,seconds=300):
    env=sanitized_env()
    for path in ('qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py',
                 'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'):
        if not (ROOT/path).is_file():
            print('[HOLD] MISSING_ORIGINAL_FAST_MODULE '+path,flush=True);return 2
    executor=verify_executor()
    print('[ORACLE-126] RESTORE_ORIGINAL_Q25_Q20_SINGLE_HYDRATION_WS_FAST_LANE',flush=True)
    print('[DISCARD] ORACLE_119_THROUGH_125_SDK_POLLING_SCANNER_NOT_LAUNCHED',flush=True)
    print('[GUARD] SIGNING=FALSE BROADCAST=FALSE EXECUTOR='+executor,flush=True)
    print('[AUX] independent Mriya + universal + lifecycle + replenishment',flush=True)
    scanner=launch([sys.executable,'-m',MRIYA],env)
    # ORACLE-129: independent, 30-second bounded replenishment OS process.
    # Does not block Q25/Q20 and never accesses signing credentials.
    helper=launch([sys.executable, str(ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py'),'--delay','45'],env)
    print('[REPLENISH_129] separate_process=True target_period_seconds=30',flush=True)
    count=0;failure_streak=0
    try:
        while not STOP.is_set():
            count+=1
            if scanner.poll() is not None:
                print('[MRIYA_RESTART] exit='+str(scanner.returncode),flush=True)
                scanner=launch([sys.executable,'-m',MRIYA],env)
            print('[FAST_PATH] session='+str(count)+' q25/q20 original cache+event pricing',flush=True)
            # q25 performs single hydration and invokes original latest-state Q20.
            # Restart with controlled backoff; it will never run the SDK polling lane.
            p=launch([sys.executable,'-m',FAST,'--seconds',str(seconds)],env)
            rc=p.wait()
            if STOP.is_set():break
            if rc:
                failure_streak=min(failure_streak+1,5)
                hold=min(120,8*2**(failure_streak-1))
                print('[FAST_RECOVERY] exit='+str(rc)+' wait_seconds='+str(hold),flush=True)
            else:
                failure_streak=0;hold=2
            write_report({'session':count,'fast_exit_code':rc,
                          'fast_restart_backoff_seconds':hold,
                          'mriya_running':scanner.poll() is None,
                          'executor_gate':executor,
                          'verified_profitable_trade':False})
            if once:return 0 if rc==0 else 2
            STOP.wait(hold)
    except KeyboardInterrupt:
        print('[STOP] ORACLE-126 original scanner stopped',flush=True)
    finally:
        STOP.set()
        for p in SUBPROCS:
            if p.poll() is None:
                try:p.terminate();p.wait(timeout=3)
                except (OSError,subprocess.TimeoutExpired):
                    p.kill()
    return 0


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--watch',action='store_true')
    ap.add_argument('--once',action='store_true')
    ap.add_argument('--seconds',type=int,default=3600)
    ap.add_argument('--trade',action='store_true')
    a=ap.parse_args()
    if a.trade:
        print('[HOLD] EXECUTOR_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST',flush=True)
        return 2
    if not 10<=a.seconds<=3600:print('[HOLD] INVALID_SESSION_SECONDS');return 2
    return run(a.once,a.seconds)
if __name__=='__main__':raise SystemExit(main())
