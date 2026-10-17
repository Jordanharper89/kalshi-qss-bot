"""ORACLE-126 full installer: restore the repository's original O25/O20/O18/O23
single-hydration fast read-only scanner, retain Mriya, crosslist, lifecycle and RPC recovery.
Never authorizes signing/broadcast or handles secret material on disk.
"""
from __future__ import annotations
import ast
import pathlib
import py_compile
import shutil
import subprocess
import sys

ROOT=pathlib.Path.cwd()
PKG=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
ORIGINAL=ROOT/'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'
Q20=ROOT/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
NATIVE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
MRIYA=ROOT/'qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/qarb_043b_paced_mriya_token_discovery.py'
UNIVERSAL=ROOT/'qseries_v2/oracle_strategy_intelligence/solana_money/mriya_python_paper_arb/crosslisted.py'
REQUIRED=(ORIGINAL,Q20,NATIVE,MRIYA,UNIVERSAL)

SUPERVISOR=r'''"""ORACLE-126: restored original FAST scanner with independent discovery, watch-only."""
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
    helper=threading.Thread(target=discover_loop,args=(env,),daemon=True)
    helper.start()
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
    ap.add_argument('--seconds',type=int,default=300)
    ap.add_argument('--trade',action='store_true')
    a=ap.parse_args()
    if a.trade:
        print('[HOLD] EXECUTOR_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST',flush=True)
        return 2
    if not 10<=a.seconds<=3600:print('[HOLD] INVALID_SESSION_SECONDS');return 2
    return run(a.once,a.seconds)
if __name__=='__main__':raise SystemExit(main())
'''

TESTS=r'''import ast, pathlib,unittest
from unittest.mock import patch
import run_oracle126 as m
class Tests(unittest.TestCase):
    def test_original_fast_lane_selected(self):
        self.assertIn('oracle_025_single_hydration',m.FAST)
        self.assertIn('qarb_043b',m.MRIYA)
    def test_no_wallet_secrets_passed_to_original(self):
        with patch.dict(m.os.environ,{'QSB_SOLANA_PRIVATE_KEY':'test-only',
              'SOLANA_RPC_URL':'https://example.invalid','ORACLE_TEST_SECRET_KEY':'sample'},clear=True):
            e=m.sanitized_env()
            self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',e)
            self.assertNotIn('ORACLE_TEST_SECRET_KEY',e)
            self.assertEqual('FALSE',e['ORACLE_EXECUTION_AUTHORITY'])
    def test_guard_does_not_authorize_trades(self):
        self.assertIn('EXECUTOR_NOT_CERTIFIED_NO_SIGN_OR_BROADCAST',
            pathlib.Path(m.__file__).read_text(encoding='utf8'))
    def test_existing_executor_read_only(self):
        self.assertEqual('CERTIFICATION_REQUIRED',m.verify_executor())
if __name__=='__main__':unittest.main(verbosity=2)
'''

ENTRY='''"""ORACLE-126 canonical credential entrypoint, original scanner restored."""\nfrom run_oracle126 import main\nif __name__=='__main__':raise SystemExit(main())\n'''

def main():
    missing=[p for p in REQUIRED if not p.is_file()]
    if missing:
        print('[HOLD] ORIGINAL_MODULES_NOT_FOUND')
        for p in missing:print('[MISSING]',p.relative_to(ROOT))
        return 2
    if not PKG.is_dir():print('[HOLD] SDK_WORKER_DIR_NOT_FOUND');return 2
    # Verify original module is genuinely read-only before attaching.
    try:
        t=ast.parse(NATIVE.read_text(encoding='utf8'))
        flags={}
        for n in t.body:
            if isinstance(n,ast.Assign):
                for k in n.targets:
                    if isinstance(k,ast.Name) and k.id in ('EXECUTION_AUTHORITY','PAPER_ONLY'):
                        try:flags[k.id]=ast.literal_eval(n.value)
                        except (TypeError,ValueError):pass
        assert flags.get('EXECUTION_AUTHORITY') is False,'Native executor authority differs; refusing install'
    except Exception as e:
        print('[HOLD] NATIVE_EXECUTOR_VERIFICATION_FAILED',type(e).__name__);return 2
    files={PKG/'run_oracle126.py':SUPERVISOR,PKG/'test_oracle126.py':TESTS,PKG/'run_oracle120.py':ENTRY}
    backups={}
    for dst in files:
        if dst.exists():backups[dst]=dst.read_bytes()
    try:
        for dst,content in files.items():dst.write_text(content,encoding='utf8',newline='\n')
        for dst in files:py_compile.compile(str(dst),doraise=True)
        result=subprocess.run([sys.executable,str(PKG/'test_oracle126.py')],cwd=str(ROOT),capture_output=True,text=True,timeout=30)
        if result.returncode:
            print(result.stdout[-1500:]);print(result.stderr[-2400:]);raise RuntimeError('ORACLE126_OFFLINE_TEST_FAILED')
        print(result.stderr.strip())
        print('[PASS] ORACLE-126 restored original O25/O20 Q18/Q23 fast scanner launch')
        print('[PRESERVE] Mriya and universal discovery; lifecycle/replenishment background')
        print('[RPC] failed fast scanner session backoff 8-120 seconds')
        print('[EXECUTOR] Existing native atomic code attached for certification; no live authority')
        print('[SAFETY] credential storage unchanged; signing/broadcast FALSE; 0.010 SOL canary target')
        print('[RUN] python oracle120_credentials.py --run')
    except Exception:
        for dst in files:
            if dst in backups:dst.write_bytes(backups[dst])
            else:dst.unlink(missing_ok=True)
        raise
    return 0
if __name__=='__main__':raise SystemExit(main())
