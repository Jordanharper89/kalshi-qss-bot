"""ORACLE-383 complete executor-only replacement: Pump SDK identity/readiness and RPC pacing.

Preserves ORACLE-382 staged Q25 canonical native warm and ORACLE-322 frozen scanner.
No private key access, signing, broadcast, funded trades, source-health override,
or weakening of fee/freshness/atomic guards. Runtime changes are reversible.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET=ROOT/'oracle_383_sdk_rpc_native_bridge.py'
SDK_HOME=Path('qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native')
SDK_ORIGINAL=SDK_HOME/'sae003_pump_exact_quote_worker.mjs'
SDK_ISOLATED=SDK_HOME/'oracle_383_public_wallet_pump_worker.mjs'
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_383_sdk_rpc_native_report.json')
UPSTREAM_REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_382_capacity_reconciliation.json')
SYSTEM_USER='11111111111111111111111111111111'
USER_START='const USER=new PublicKey(\n  "'+SYSTEM_USER+'"\n);'
USER_REPLACEMENT=('const wallet=process.env.QSB_SOLANA_WALLET;\n'
                  'if(!wallet)throw new Error("ORACLE383_PUBLIC_WALLET_REQUIRED");\n'
                  'const USER=new PublicKey(wallet);')
AUTHORITY=SIGNING=BROADCAST=False
CANARY_LAMPORTS=10_000_000
PUBLIC_KEY_RE=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SDK_REASON_MAP=(('429','SDK_HTTP_429'),('TOO MANY REQUESTS','SDK_HTTP_429'),
                ('SAE003_POOL_NOT_WARM','SDK_POOL_NOT_WARM'),
                ('SAE003_SWAP_STATE_EMPTY','SDK_SWAP_STATE_EMPTY'),
                ('SAE003_POOL_STATE_EMPTY','SDK_POOL_STATE_EMPTY'),
                ('SAE003_GLOBAL_CONFIG_EMPTY','SDK_GLOBAL_CONFIG_EMPTY'),
                ('SAE003_FEE_CONFIG_EMPTY','SDK_FEE_CONFIG_EMPTY'),
                ('SAE003_SELL_QUOTE_EMPTY','SDK_SELL_QUOTE_EMPTY'),
                ('SAE003_SELL_BASE_NONPOSITIVE','SDK_SELL_BASE_NONPOSITIVE'),
                ('SAE003_BUY_QUOTE_EMPTY','SDK_BUY_QUOTE_EMPTY'),
                ('PUMP_SDK_RESPONSE_ORDER','SDK_RESPONSE_ORDER'),
                ('PUMP_SDK_WORKER_DIED','SDK_CHILD_EXIT'))
SAFE_CHILD_NAMES=('PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','HOME',
                  'USERPROFILE','APPDATA','LOCALAPPDATA','NODE_PATH',
                  'SOLANA_RPC_URL','QSB_SOLANA_WALLET')

class Hold(RuntimeError):pass

def deps():
    return importlib.import_module(PKG+'.oracle_382_staged_native_capacity')

def modules():
    r=importlib.import_module(PKG+'.runtime')
    q18=importlib.import_module('qseries_v2.oracle_execution.oracle_018_exact_sdk_hot_lane_cutover')
    c=importlib.import_module('qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine.core')
    return r,q18,c

def node_source(original):
    if original.count(USER_START)!=1:raise Hold('SDK_LEGACY_WORKER_IDENTITY_CONTRACT_CHANGED')
    out=original.replace(USER_START,USER_REPLACEMENT)
    if out.count(USER_REPLACEMENT)!=1:raise Hold('SDK_ISOLATED_IDENTITY_REPLACEMENT_FAILED')
    if 'const rl=readline.createInterface' not in out or 'sellBaseInput' not in out:
        raise Hold('SDK_EXISTING_PRICER_CONTRACT_CHANGED')
    return out

def write_atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False) as f:
        f.write(data);tmp=f.name
    os.replace(tmp,path)

def json_atomic(path,obj):
    write_atomic(path,json.dumps(obj,sort_keys=True,indent=2,default=str).encode())

def safe_json(path):
    try:
        val=json.loads(Path(path).read_text(encoding='utf8'))
        return val if isinstance(val,dict) else {}
    except (OSError,ValueError,TypeError):return {}

def child_env(wallet,source=None):
    if not isinstance(wallet,str) or not PUBLIC_KEY_RE.fullmatch(wallet):raise Hold('PUBLIC_WALLET_REQUIRED')
    source=os.environ if source is None else source
    out={k:source[k] for k in SAFE_CHILD_NAMES if k in source}
    out['QSB_SOLANA_WALLET']=wallet
    if not out.get('SOLANA_RPC_URL','').startswith('https://'):
        raise Hold('RPC_HTTPS_URL_REQUIRED')
    return out

def sdk_failure(exc):
    """Never emit arbitrary RPC URL, API-key, SDK stack, or token values."""
    value=str(exc).upper()
    for marker,code in SDK_REASON_MAP:
        if marker in value:return code
    if isinstance(exc,subprocess.TimeoutExpired) or isinstance(exc,TimeoutError):return 'SDK_TIMEOUT'
    if isinstance(exc,(BrokenPipeError,EOFError,OSError)):return 'SDK_IO_FAILURE'
    return 'SDK_UNCLASSIFIED_FAILURE'

class RpcTraffic:
    """One Python core.http request budget, fail-fast on hot lane, bounded on warm lane.

    Node's OnlinePumpAmmSdk uses independent internal HTTP calls; pool-warm
    starts are separately reserved as an estimate, never misreported as exact RPCs.
    ORACLE-322 is another process and not covered by this local budget.
    """
    def __init__(self,rate=6.,burst=6.,clock=None,sleep=None):
        if not 1<=rate<=30 or not 1<=burst<=30:raise Hold('RPC_LIMIT_INVALID')
        self.clock=clock or time.monotonic;self.sleep=sleep or time.sleep
        self.rate=float(rate);self.burst=float(burst);self.credit=float(burst)
        self.previous=self.clock();self.cooldown_until=0.;self.lock=threading.RLock()
        self.events=Counter();self.timeline=deque(maxlen=30)
        self.sdk_warm_pool=set();self.sdk_failed={};self.sdk_times_ms=[]
    def acquire(self,units=1.,warm=False):
        if not 0<units<=self.burst:raise Hold('RPC_RESERVATION_INVALID')
        # MainThread (startup) and only canonical replenisher can wait.
        # Native pricing worker NEVER waits for RPC tokens or stale retries.
        max_wait=12. if warm else 0.
        t0=self.clock()
        while True:
            with self.lock:
                now=self.clock();dt=max(0,now-self.previous);self.previous=now
                self.credit=min(self.burst,self.credit+dt*self.rate)
                wait=max(0.,self.cooldown_until-now)
                if not wait and self.credit>=units:
                    self.credit-=units;self.events['reservations_admitted']+=1
                    self.events['units_reserved']+=int(units*1000)
                    return
                if not warm or self.clock()-t0+max(wait,(units-self.credit)/self.rate)>max_wait:
                    self.events['requests_held_no_wait']+=1
                    raise Hold('RPC_BUDGET_OR_429_COOLDOWN_REQUIRE_FRESH_EVENT')
                nap=max(.01,min(.5,max(wait,(units-self.credit)/self.rate)))
            self.sleep(nap)
    def mark_429(self,exc,rate_delay):
        sec=rate_delay(exc,self.events['rpc_http_429']+1)
        with self.lock:
            self.events['rpc_http_429']+=1
            self.cooldown_until=max(self.cooldown_until,self.clock()+sec)
        return sec
    def observe(self,label):
        with self.lock:self.events[label]+=1
    def snapshot(self):
        with self.lock:
            return {'scope':'EXECUTOR_PYTHON_CORE_HTTP_PLUS_ESTIMATED_NODE_WARM_STARTS',
                'does_not_control_scanner_322_or_node_internal_http':True,
                'rate_http_per_second':self.rate,'burst':self.burst,
                'cooldown_remaining_s':round(max(0.,self.cooldown_until-self.clock()),2),
                'counts':dict(self.events),'sdk_ready_pool_count':len(self.sdk_warm_pool),
                'sdk_warm_failed_by_pool_prefix':{k[:12]:v for k,v in self.sdk_failed.items()},
                'sdk_warm_latency_ms':{'samples':len(self.sdk_times_ms),
                  'p50':percentile(self.sdk_times_ms,.5),'p95':percentile(self.sdk_times_ms,.95)}}

def percentile(values,q):
    if not values:return None
    a=sorted(values);return round(a[min(len(a)-1,int((len(a)-1)*q+.999999))],2)

class Bridge:
    def __init__(self,wallet,rate=6.):
        self.wallet=wallet
        self.traffic=RpcTraffic(rate=rate,burst=6.)
        self.orig=None;self.node_original_hash=None
        self.warm_calls=0;self.sdk_gate_holds=0
    def __enter__(self):
        runtime,q18,c=modules()
        if getattr(q18,'_worker',None) is not None:
            raise Hold('SDK_ALREADY_STARTED_FRESH_EXECUTOR_PROCESS_REQUIRED')
        if not SDK_ISOLATED.is_file() or not SDK_ORIGINAL.is_file():
            raise Hold('SDK_ISOLATED_WORKER_NOT_INSTALLED')
        if SDK_ISOLATED.read_text(encoding='utf8')!=node_source(SDK_ORIGINAL.read_text(encoding='utf8')):
            raise Hold('SDK_ISOLATED_WORKER_INTEGRITY_FAILED')
        env=child_env(self.wallet)
        originals=(runtime.install_proven_hot_math,q18.PumpSdkWorker.__init__,
                   q18.PumpSdkWorker.request,q18.WORKER_JS,c.http)
        self.orig=originals
        original_hot, original_init, original_request, original_path, original_http=originals
        traffic=self.traffic
        def init(worker):
            # The public wallet is passed. Private-key and mnemonic variables
            # are not copied into the child environment.
            worker.proc=subprocess.Popen(['node',SDK_ISOLATED.name],cwd=str(q18.NODEDIR),
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                text=True,bufsize=1,env=env)
            worker.lock=threading.Lock();worker.seq=0
        def request(worker,payload):
            op=payload.get('op') if isinstance(payload,dict) else None
            pool=payload.get('pool') if isinstance(payload,dict) else None
            if op in ('sell','buy') and pool not in traffic.sdk_warm_pool:
                self.sdk_gate_holds+=1
                raise Hold('PUMP_SDK_POOL_NOT_WARM_FRESH_EVENT_REQUIRED')
            try:
                result=original_request(worker,payload)
            except Exception as exc:
                reason=sdk_failure(exc)
                traffic.observe('sdk_failure_'+reason)
                if reason=='SDK_HTTP_429':
                    traffic.mark_429(exc,lambda e,n:min(120.,2**min(6,n)))
                if op=='warm' and isinstance(pool,str):traffic.sdk_failed[pool]=reason
                if reason=='SDK_POOL_NOT_WARM' and isinstance(pool,str):
                    traffic.sdk_warm_pool.discard(pool)
                raise Hold(reason) from None
            if op=='warm' and isinstance(pool,str):
                traffic.sdk_warm_pool.add(pool);traffic.sdk_failed.pop(pool,None)
            return result
        def http(url,method='GET',body=None,timeout=15):
            name=threading.current_thread().name
            warm=name=='MainThread' or name=='oracle380-rpc-budget-replenisher'
            traffic.acquire(warm=warm)
            try:
                result=original_http(url,method,body,timeout)
                traffic.observe('python_http_completed')
                return result
            except Exception as exc:
                if getattr(exc,'code',None)==429 or getattr(exc,'status',None)==429:
                    # Honor provider Retry-After, but never retry a stale candidate.
                    m380=importlib.import_module(PKG+'.oracle_380_rpc_admission_diagnostics')
                    traffic.mark_429(exc,m380.rate_delay)
                    raise Hold('RPC_HTTP_429_BACKOFF_REQUIRE_NEW_EVENT') from None
                traffic.observe('python_http_other_failure')
                raise
        def hot(state):
            warmed=original_hot(state)
            if not isinstance(state,dict):raise Hold('SDK_HOT_STATE_INVALID')
            for pair in state.get('pairs') or []:
                token=str(getattr(pair,'token',''))
                pool=str(getattr(pair,'pump_pool',''))
                if not token or not PUBLIC_KEY_RE.fullmatch(pool):
                    raise Hold('SDK_CANONICAL_PAIR_IDENTITY_INVALID')
                if token not in runtime.READY_TOKENS:continue
                if pool in traffic.sdk_warm_pool:continue
                # Account hydration already completed. One exact SDK pool warm
                # before native-state publication; no candidate-thread warming.
                name=threading.current_thread().name
                if name not in ('MainThread','oracle380-rpc-budget-replenisher'):
                    raise Hold('SDK_WARM_ONLY_OUTSIDE_CANDIDATE_LANE')
                traffic.acquire(3.,warm=True)  # estimated Node RPC reservation
                start=time.perf_counter()
                try:q18.worker().warm(pool)
                except Exception as exc:
                    runtime.READY_TOKENS.discard(token)
                    reason=(str(exc) if isinstance(exc,Hold) and
                            re.fullmatch(r'[A-Z][A-Z0-9_]{2,90}',str(exc))
                            else sdk_failure(exc))
                    traffic.observe('sdk_warm_rejected_native_readiness')
                    print('[ORACLE383_SDK_WARM_HOLD]',json.dumps({
                        'token_prefix':token[:12],'pump_pool_prefix':pool[:12],
                        'reason':reason},sort_keys=True),flush=True)
                    raise Hold('SDK_PREWARM_FAILURE_REQUIRE_REPLENISH') from None
                finally:
                    with traffic.lock:
                        traffic.sdk_times_ms.append((time.perf_counter()-start)*1000)
                        traffic.sdk_times_ms=traffic.sdk_times_ms[-100:]
                self.warm_calls+=1
                print('[ORACLE383_SDK_POOL_WARM]',json.dumps({'token_prefix':token[:12],
                    'pump_pool_prefix':pool[:12], 'sdk_ready':True},sort_keys=True),flush=True)
            return warmed
        q18.WORKER_JS=SDK_ISOLATED
        q18.PumpSdkWorker.__init__=init
        q18.PumpSdkWorker.request=request
        c.http=http
        runtime.install_proven_hot_math=hot
        return self
    def __exit__(self,*args):
        if self.orig is not None:
            runtime,q18,c=modules()
            # Stop this session's isolated SDK child before restoring the
            # original class; no lingering worker with a different wallet.
            worker=getattr(q18,'_worker',None)
            if worker is not None:
                try:worker.close()
                except Exception:self.traffic.observe('sdk_worker_close_failure')
                q18._worker=None
            (runtime.install_proven_hot_math,q18.PumpSdkWorker.__init__,
             q18.PumpSdkWorker.request,q18.WORKER_JS,c.http)=self.orig
            self.orig=None
        return False

def install():
    if not (ROOT/'oracle_382_staged_native_capacity.py').is_file():
        raise Hold('ORACLE382_INSTALLED_BASELINE_REQUIRED')
    if not SDK_ORIGINAL.is_file():raise Hold('Q18_ORIGINAL_NODE_WORKER_MISSING')
    body=node_source(SDK_ORIGINAL.read_text(encoding='utf8'))
    src=Path(__file__).resolve().read_bytes()
    compile(src.decode('utf8'),str(TARGET),'exec')
    write_atomic(TARGET,src) if Path(__file__).resolve()!=TARGET.resolve() else None
    write_atomic(SDK_ISOLATED,body.encode('utf8'))
    print('[ORACLE383_INSTALL_PASS]',json.dumps({'python_target':str(TARGET),
          'isolated_node_target':str(SDK_ISOLATED),
          'sdk_sha256':hashlib.sha256(body.encode()).hexdigest()[:16]},sort_keys=True),flush=True)

def audit():
    if not TARGET.is_file() or TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise Hold('ORACLE383_INSTALL_INTEGRITY_FAILED')
    if not SDK_ISOLATED.is_file() or not SDK_ORIGINAL.is_file() or (
        SDK_ISOLATED.read_text(encoding='utf8')!=node_source(SDK_ORIGINAL.read_text(encoding='utf8'))):
        raise Hold('ORACLE383_SDK_WORKER_INTEGRITY_FAILED')
    if (AUTHORITY,SIGNING,BROADCAST,CANARY_LAMPORTS)!=(False,False,False,10000000):
        raise Hold('ORACLE383_AUTHORITY_INVARIANT_FAILED')
    dep=deps();dep.audit()
    print('[ORACLE383_AUDIT_PASS] FROZEN322 SDK_PUBLIC_WALLET_CHILD '
          'SDK_POOL_READINESS CORE_HTTP_BUDGET GUARDED_NATIVE_PIPELINE NO_SIGN_NO_BROADCAST',flush=True)

def node_check():
    p=subprocess.run(['node','--check',str(SDK_ISOLATED)],capture_output=True,text=True,timeout=20)
    if p.returncode:raise Hold('ISOLATED_SDK_NODE_SYNTAX_FAILED')
    print('[ORACLE383_NODE_CHECK_PASS] ISOLATED_SDK_WORKER_SYNTAX',flush=True)

def tests():
    class T(unittest.TestCase):
        def test_node_rewrite(self):
            src='header\n'+USER_START+'\n'+('const rl=readline.createInterface\nsellBaseInput')
            d=node_source(src);self.assertNotIn(USER_START,d);self.assertIn('QSB_SOLANA_WALLET',d)
        def test_node_source_nonmatching_hold(self):
            with self.assertRaises(Hold):node_source('different SDK')
        def test_node_retains_original_sdk_methods(self):
            s=node_source(USER_START+'\nconst rl=readline.createInterface\nsellBaseInput')
            self.assertIn('sellBaseInput',s)
        def test_wallet_valid(self):
            e=child_env('A'*43,{'PATH':'p','SOLANA_RPC_URL':'https://rpc','QSB_SOLANA_PRIVATE_KEY':'secret'})
            self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',e)
        def test_child_drops_secrets(self):
            e=child_env('A'*43,{'PATH':'p','SOLANA_RPC_URL':'https://rpc','API_KEY':'secret','MNEMONIC':'phrase'})
            self.assertNotIn('API_KEY',e);self.assertNotIn('MNEMONIC',e)
        def test_invalid_wallet(self):
            with self.assertRaises(Hold):child_env('BAD',{'SOLANA_RPC_URL':'https://rpc'})
        def test_invalid_rpc(self):
            with self.assertRaises(Hold):child_env('A'*43,{'SOLANA_RPC_URL':'http://rpc'})
        def test_sdk_failure_429(self):self.assertEqual(sdk_failure(RuntimeError('PUMP_SDK_WORKER:429 Too Many Requests')),'SDK_HTTP_429')
        def test_sdk_failure_cold(self):self.assertEqual(sdk_failure(RuntimeError('SAE003_POOL_NOT_WARM:wallet')),'SDK_POOL_NOT_WARM')
        def test_sdk_failure_fee(self):self.assertEqual(sdk_failure(RuntimeError('SAE003_FEE_CONFIG_EMPTY')),'SDK_FEE_CONFIG_EMPTY')
        def test_sdk_failure_redacts(self):self.assertNotIn('SUPERSECRET',sdk_failure(ValueError('url ?api-key=SUPERSECRET')))
        def test_p50(self):self.assertEqual(percentile([1,2,3],.5),2.)
        def test_empty_percentile(self):self.assertIsNone(percentile([],.5))
        def test_rate_limit(self):
            tm=[100.];budget=RpcTraffic(rate=2,burst=2,clock=lambda:tm[0],sleep=lambda t:None)
            budget.acquire();budget.acquire()
            with self.assertRaises(Hold):budget.acquire()
            tm[0]=101.;budget.acquire()
        def test_429_cooldown(self):
            c=RpcTraffic(clock=lambda:100.,sleep=lambda t:None)
            c.mark_429(RuntimeError(),lambda x,n:40.)
            with self.assertRaises(Hold):c.acquire()
        def test_rate_delay_derived(self):
            c=RpcTraffic();self.assertEqual(c.mark_429(RuntimeError(),lambda x,n:1),1)
        def test_rate_invalid(self):
            with self.assertRaises(Hold):RpcTraffic(rate=0)
        def test_budget_reservation_bounded(self):
            with self.assertRaises(Hold):RpcTraffic().acquire(units=7.)
        def test_no_trade_auth(self):self.assertEqual((AUTHORITY,SIGNING,BROADCAST),(False,False,False))
        def test_canary(self):self.assertEqual(CANARY_LAMPORTS,10000000)
        def test_not_scanner_mutation(self):
            import inspect
            self.assertNotIn('scanner_status.json',inspect.getsource(Bridge))
        def test_sdk_contract_not_exporting_secrets(self):
            import inspect
            source=inspect.getsource(Bridge.__enter__)
            self.assertNotIn('PRIVATE_KEY',source)
        def test_install_sources_immutable(self):
            source=Path(__file__).read_text(encoding='utf8')
            self.assertIn('ORACLE-322',source)
        def test_live_seam_warming_and_restoration(self):
            from types import SimpleNamespace as S
            class FakeWorker:
                def request(self,row):return {'ok':True}
                def warm(self,pool):return self.request({'op':'warm','pool':pool})
            instance=FakeWorker()
            class FakeSDK:
                pass
            sdk=FakeSDK();sdk._worker=None;sdk.PumpSdkWorker=FakeWorker
            sdk.NODEDIR=SDK_HOME;sdk.WORKER_JS=SDK_ORIGINAL
            sdk.worker=lambda:instance
            module=S(READY_TOKENS={'T'*43},install_proven_hot_math=lambda state:[{'token':'T'*43,'program':'SPL'}])
            core=S(http=lambda url,method='GET',body=None,timeout=15: {'ok':True})
            pair=S(token='T'*43,pump_pool='P'*43)
            with tempfile.TemporaryDirectory() as td:
                orig=Path(td)/'original.mjs';isolated=Path(td)/'isolated.mjs'
                orig.write_text(USER_START+'\nconst rl=readline.createInterface\nsellBaseInput',encoding='utf8')
                isolated.write_text(node_source(orig.read_text(encoding='utf8')),encoding='utf8')
                oldhot=module.install_proven_hot_math;oldreq=FakeWorker.request;oldhttp=core.http
                with patch(__name__+'.modules',return_value=(module,sdk,core)), \
                     patch(__name__+'.SDK_ORIGINAL',orig),patch(__name__+'.SDK_ISOLATED',isolated), \
                     patch.dict(os.environ,{'SOLANA_RPC_URL':'https://rpc.example'}):
                    with Bridge('A'*43) as bridge:
                        with self.assertRaises(Hold):instance.request({'op':'sell','pool':'P'*43})
                        module.install_proven_hot_math({'pairs':[pair]})
                        self.assertEqual(bridge.traffic.snapshot()['sdk_ready_pool_count'],1)
                        self.assertTrue(instance.request({'op':'sell','pool':'P'*43})['ok'])
                        self.assertEqual(core.http('https://rpc.example'),{'ok':True})
                    self.assertIs(module.install_proven_hot_math,oldhot)
                    self.assertIs(FakeWorker.request,oldreq)
                    self.assertIs(core.http,oldhttp)
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE383_TEST_PASS]' if r.wasSuccessful() else '[ORACLE383_TEST_FAIL]',r.testsRun,flush=True)
    return 0 if r.wasSuccessful() else 1

def inspect():
    r=safe_json(REPORT)
    old=safe_json(UPSTREAM_REPORT)
    print('[ORACLE383_INSPECT]',json.dumps({'latest_status':r.get('status'),
        'last_native_pairs':((old.get('replenishment') or [{}])[-1].get('native_pairs_current')
                             if old.get('replenishment') else None),
        'last_replenishment':((old.get('replenishment') or [{}])[-1].get('status')
                             if old.get('replenishment') else None),
        'sdk_ready_pools':r.get('guard_metrics',{}).get('sdk_ready_pool_count'),
        'rpc_counts':r.get('guard_metrics',{}).get('counts')},sort_keys=True),flush=True)

def run(minutes,poll_ms,wallet):
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:raise Hold('RUN_CONFIG_INVALID')
    audit()
    base=deps()
    probe=base.dep().scanner_bus_probe()
    if probe.get('validator')!='PASS':raise Hold('SCANNER_HEALTH_GATE_FAILED')
    started=time.monotonic();code=2;bridge=Bridge(wallet)
    try:
        with bridge:
            code=base.run(minutes,poll_ms,wallet)
    finally:
        prior=safe_json(UPSTREAM_REPORT)
        report={'build':'ORACLE383','status':'READ_ONLY_SESSION_DONE' if code==0 else 'READ_ONLY_HOLD',
          'based_on':'ORACLE382','duration_s':round(time.monotonic()-started,2),
          'base_native_stage':((prior.get('replenishment') or [{}])[-1].get('cap_attempts',[])
                               if prior.get('replenishment') else []),
          'native_pairs_final':((prior.get('replenishment') or [{}])[-1].get('native_pairs_current')
                               if prior.get('replenishment') else None),
          'guard_metrics':bridge.traffic.snapshot(),'sdk_warm_calls':bridge.warm_calls,
          'sdk_gate_holds':bridge.sdk_gate_holds,'first_canary_lamports':CANARY_LAMPORTS,
          'scanner322_modified':False,'private_key_used':False,'signing':False,
          'broadcast':False,'execution_authority':False,'native_profit_certified':False,
          'report_warning':'RPC shared with independent scanner process not globally budgeted; Node SDK network per warm measured as reserved estimates'}
        json_atomic(REPORT,report)
        print('[ORACLE383_RUNTIME_REPORT]',REPORT,flush=True)
        print('[ORACLE383_RUNTIME_COUNTS]',json.dumps({'sdk_warm_calls':bridge.warm_calls,
             'sdk_gate_holds':bridge.sdk_gate_holds,'native_pairs_final':report['native_pairs_final'],
             'rpc':report['guard_metrics']},sort_keys=True),flush=True)
        print('[ORACLE383_STATUS]',report['status'],flush=True)
    return code

def main():
    ap=argparse.ArgumentParser()
    for x in ('install','test','audit','node-check','sdk-check','burst','health-gate','inspect','run'):
        ap.add_argument('--'+x,action='store_true')
    ap.add_argument('--minutes',type=int,default=5)
    ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET',''))
    a=ap.parse_args()
    if not any((a.install,a.test,a.audit,a.node_check,a.sdk_check,a.burst,a.health_gate,a.inspect,a.run)):
        ap.error('ACTION_REQUIRED')
    if a.install:install()
    if a.test and tests():return 1
    if a.audit:audit()
    if a.node_check:node_check()
    if a.sdk_check:deps().dep().imports().import_deps()[0].sdk_check_visible()
    if a.burst:print('[ORACLE383_BURST_PASS]',json.dumps(deps().dep().imports().import_deps()[0].burst(),sort_keys=True),flush=True)
    if a.health_gate:
        h=deps().dep().scanner_bus_probe()
        if h.get('validator')!='PASS':
            print('[ORACLE383_SCANNER_HEALTH_HOLD]',json.dumps(h,sort_keys=True),flush=True);return 2
        print('[ORACLE383_SCANNER_HEALTH_PASS]',json.dumps(h,sort_keys=True),flush=True)
    if a.inspect:inspect()
    if a.run:return run(a.minutes,a.poll_ms,a.wallet_pubkey)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('[ORACLE383_HOLD]',type(exc).__name__,flush=True)
        raise SystemExit(2)
