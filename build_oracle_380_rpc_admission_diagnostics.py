"""ORACLE-380 complete executor-only full installer.

Canonical ORACLE-379C remains the tested capacity foundation. Install this
module in full; runtime composes replacements, never edits scanner or 379 files.
Scope: cooperative background replenishment, bounded 429 handling and separate
stage-specific (redacted) diagnostics. No key use, signing, broadcast or trades.
"""
from __future__ import annotations
import argparse
import collections
from email.utils import parsedate_to_datetime
import importlib
import json
import os
from pathlib import Path
import random
import re
import sys
import tempfile
import threading
import time
import traceback
import unittest
from unittest.mock import patch

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET=ROOT/'oracle_380_rpc_admission_diagnostics.py'
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_380_capacity_and_rpc.json')
ORIGINAL_REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_379_capacity_report.json')
CANARY=10_000_000
AUTHORITY=SIGNING=BROADCAST=False
MIN_REDISCOVERY_SEC=60.0
FIRST_REDISCOVERY_DELAY_SEC=30.0
MAX_BACKOFF_SEC=300.0
CODE=re.compile(r'^[A-Z][A-Z0-9_]{2,90}$')
SECRET=re.compile(r'(?i)PRIVATE.?KEY|API.?KEY|SECRET|TOKEN_VALUE|MNEMONIC|SEED|AUTHORIZATION')

class Hold(RuntimeError):pass

def json_write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=p.parent,delete=False) as f:
        json.dump(obj,f,indent=2,sort_keys=True,default=str); tmp=f.name
    os.replace(tmp,p)

def import_deps():
    m379=importlib.import_module(PKG+'.oracle_379_five_goal_executor')
    m378=importlib.import_module(PKG+'.oracle_378_native_reverse_atomic')
    return m379,m378

def rate_delay(exc,failures=1,rng=None):
    """Honor Retry-After seconds/date; bounded fallback exponential + jitter."""
    headers=getattr(exc,'headers',None)
    retry=None
    if headers is not None:
        try:retry=headers.get('Retry-After')
        except (AttributeError,TypeError):pass
    if retry is not None:
        try:seconds=float(retry)
        except (ValueError,TypeError):
            try:
                import datetime
                at=parsedate_to_datetime(str(retry))
                seconds=(at-datetime.datetime.now(at.tzinfo)).total_seconds()
            except (TypeError,ValueError,OverflowError):seconds=None
        if seconds is not None and seconds>=0:
            return min(MAX_BACKOFF_SEC,max(1.,float(seconds)))
    base=min(MAX_BACKOFF_SEC,2.**min(8,max(0,int(failures)-1)))
    rng=rng or random.Random()
    return min(MAX_BACKOFF_SEC,max(1.,base*rng.uniform(.75,1.25)))

def is_429(exc):
    return getattr(exc,'code',None)==429 or getattr(exc,'status',None)==429

def error_identity(exc,stage):
    """No arbitrary exception text: code, stage, class and trusted basename only."""
    stage=re.sub('[^A-Z0-9_]','',str(stage).upper())[:35] or 'UNKNOWN'
    code=type(exc).__name__.upper()
    if is_429(exc):code='HTTP_429'
    elif isinstance(exc,(Hold,RuntimeError)) and CODE.fullmatch(str(exc) or '') and not SECRET.search(str(exc)):
        code=str(exc)
    elif isinstance(exc,RuntimeError) and str(exc).startswith('PUMP_SDK_WORKER:'):
        code='PUMP_SDK_WORKER_FAILURE'
    elif isinstance(exc,TimeoutError):code='TIMEOUT'
    # Sanitized originating source line from traceback, no frame locals or path.
    tb=traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
    origin='UNAVAILABLE'
    for frame in reversed(tb):
        if frame.filename.replace('\\','/').split('/')[-1].startswith(('oracle_','build_oracle_')):
            name=Path(frame.filename).name
            if re.fullmatch('[a-zA-Z0-9_]+\\.py',name):origin=name+':'+str(max(0,frame.lineno));break
    return {'stage':stage,'exception_type':type(exc).__name__[:45],
            'reason':(stage+'_'+code)[:95],'source':origin}

class Replenishment:
    """One bounded, rate-aware canonical Q25 worker; never waits in trade callback."""
    def __init__(self,provider,*,clock=None,sleeper=None,delay=FIRST_REDISCOVERY_DELAY_SEC):
        self.provider=provider
        self.clock=clock or time.monotonic
        self.sleeper=sleeper or time.sleep
        self.cv=threading.Condition()
        self.pending=collections.OrderedDict()
        self.dead=False
        self.next_allowed=self.clock()+max(0,delay)
        self.attempts=0;self.failures=0;self.last_status='SCHEDULED'
        self.counts=collections.Counter();self.worker=None
        self.initial_due=True
        self.last_success=0.
    def request(self,token):
        if not isinstance(token,str) or not 20<=len(token)<=60:
            return 'REPLENISH_BAD_TOKEN_IDENTITY'
        if self.dead:return 'REPLENISH_CLOSED'
        p=self.provider
        if token in getattr(p.forward,'pairs',{}) and token in getattr(p.old,'READY_TOKENS',()):
            return 'REPLENISH_ALREADY_READY_REQUIRE_FRESH_EVENT'
        with self.cv:
            if token in self.pending:
                self.counts['duplicate_requested']+=1
                return 'REPLENISH_PENDING_FRESH_EVENT_REQUIRED'
            if len(self.pending)>=512:
                self.counts['requests_capacity_rejected']+=1
                return 'REPLENISH_REQUEST_CAPACITY_REJECTED'
            self.pending[token]=self.clock();self.counts['requested']+=1;self.cv.notify()
        return 'REPLENISH_QUEUED_FRESH_EVENT_REQUIRED'
    def start(self):
        with self.cv:
            if self.worker is not None:return
            self.worker=threading.Thread(target=self._run,daemon=True,name='oracle380-rpc-budget-replenisher')
            self.worker.start()
    def close(self):
        with self.cv:self.dead=True;self.cv.notify_all()
        if self.worker:self.worker.join(timeout=.3)
    def _run(self):
        while True:
            with self.cv:
                if self.dead:return
                wait=max(0,self.next_allowed-self.clock())
                if not self.initial_due and not self.pending:
                    self.cv.wait(timeout=1.);continue
                if wait:
                    self.cv.wait(timeout=min(wait,1.));continue
                self.initial_due=False
                self.attempts+=1;self.counts['attempts']+=1
                self.next_allowed=self.clock()+MIN_REDISCOVERY_SEC
            self.attempt_once()
    def attempt_once(self):
        """Network discovery outside native lock; publish under lock, fail closed on partial apply."""
        p=self.provider
        try:
            state,_=p.old.q25.q60b2.prepare_once(Path.cwd())
            if not isinstance(state,dict) or not isinstance(state.get('pairs'),(list,tuple)):
                raise Hold('CANONICAL_DISCOVERY_MALFORMED')
            newpairs=list(state['pairs'])
            native=getattr(p.forward,'pairs',{})
            existing=set(native)
            new={str(x.token):x for x in newpairs}
            if not existing.issubset(set(new)):
                self.counts['nonmonotonic_discovery_held']+=1
                self.last_status='HOLD_NONMONOTONIC_CANONICAL_DISCOVERY';return
            old_ready=set(str(x) for x in getattr(p.old,'READY_TOKENS',()))
            needs_template=any(t in new and t not in old_ready for t in self.pending)
            if not set(new)-existing and not needs_template:
                self.counts['no_new_pairs']+=1;self.last_status='NO_NEW_CANONICAL_PAIRS'
                with self.cv:
                    for k in list(self.pending):
                        if k not in new:self.pending.pop(k,None);self.counts['not_canonical']+=1
                return
            # All mutable template publication stays under the existing Q87 lock.
            # Re-check stop before publishing a network result from a closing process.
            if self.dead:return
            with p.forward.lock:
                if self.dead or getattr(p,'refresh_fatal',False):return
                try:
                    p.old.q25.bind_cached_state(state)
                    warmed=p.old.install_proven_hot_math(state)
                    p.old.prebuild_templates(state,p.forward.wallet)
                    p.old.prebuild_meteora_templates(state,p.forward.wallet,warmed)
                    programs={str(x['token']):str(x['program']) for x in warmed
                          if isinstance(x,dict) and x.get('token') and x.get('program')}
                    ready=set(str(x) for x in getattr(p.old,'READY_TOKENS',()))
                    if not set(new).issubset(ready) or not set(new).issubset(programs):
                        raise Hold('NATIVE_TEMPLATES_INCOMPLETE')
                    p.forward.state=state;p.forward.pairs=new
                    p.forward.indexes={str(x.token):i for i,x in enumerate(newpairs)}
                    p.forward.programs=programs
                except Exception:
                    p.refresh_fatal=True
                    raise Hold('CANONICAL_PREWARM_PARTIAL_MUTATION_FAIL_CLOSED') from None
            self.last_success=self.clock();self.last_status='NEW_CANONICAL_PAIRS_WARMED_REQUIRE_NEW_EVENT'
            self.counts['new_pairs_warmed']+=len(set(new)-existing)
            with self.cv:
                for k in list(self.pending):
                    if k in new:self.pending.pop(k,None);self.counts['resolved_requests']+=1
        except Exception as exc:
            self.failures+=1;detail=error_identity(exc,'DISCOVERY_PREWARM')
            if is_429(exc):
                delay=rate_delay(exc,self.failures)
                with self.cv:self.next_allowed=max(self.next_allowed,self.clock()+delay)
                self.counts['http_429']+=1;self.last_status='HOLD_429_BACKOFF'
            elif isinstance(exc,Hold) and str(exc)=='CANONICAL_PREWARM_PARTIAL_MUTATION_FAIL_CLOSED':
                self.counts['fatal_prebuild']+=1;self.last_status='HOLD_PARTIAL_MUTATION_FAIL_CLOSED'
                with self.cv:self.next_allowed=float('inf')
            else:
                self.counts['other_error']+=1;self.last_status=detail['reason']
                with self.cv:self.next_allowed=max(self.next_allowed,self.clock()+rate_delay(exc,self.failures))
    def snapshot(self):
        with self.cv:
            return {'pending_count':len(self.pending), 'counts':dict(self.counts),
                    'next_attempt_wait_s':None if self.next_allowed==float('inf') else round(max(0.,self.next_allowed-self.clock()),2),
                    'status':self.last_status,'failed_closed':bool(getattr(self.provider,'refresh_fatal',False)),
                    'last_successful_refresh':self.last_success>0,
                    'thread_running':self.worker is not None and self.worker.is_alive()}

class NativeStartBudget:
    """Nonblocking protection against repeated native bank/SDK RPC bursts.

    Admission is intentionally bounded until the provider's true account cost
    and API-key tier are measured. This does not control calls by ORACLE-322.
    """
    def __init__(self,rate=1.0,burst=2.,clock=None):
        if not .2<=rate<=10. or not 1.<=burst<=20.:raise Hold('RPC_BUDGET_INVALID')
        self.rate=float(rate);self.burst=float(burst);self.tokens=float(burst)
        self.clock=clock or time.monotonic;self.last=self.clock()
        self.lock=threading.Lock();self.denied=0;self.admitted=0
    def admit(self):
        with self.lock:
            now=self.clock();delta=max(0.,now-self.last)
            self.last=now;self.tokens=min(self.burst,self.tokens+delta*self.rate)
            if self.tokens<1.:
                self.denied+=1;return False
            self.tokens-=1.;self.admitted+=1;return True
    def snapshot(self):
        with self.lock:return {'native_starts_admitted':self.admitted,
            'native_starts_budget_held':self.denied,'rate_per_sec':self.rate,
            'burst':self.burst,'scope':'EXECUTOR_ONLY_NOT_SHARED_WITH_SCANNER'}

def provider_factory(m379,m378):
    class Factory:
        active=None
        def __init__(self,m378_arg,metrics):
            self.metrics=metrics;self.inventory=None;self.instances=[]
            Factory.active=self
        def provider_class(self):
            fact=self
            class Provider(m378.CompatibleNativeProvider):
                def __init__(self,native,wallet):
                    super().__init__(native,wallet)
                    self.refresh_fatal=False;self.refiller=None
                    self.native_budget=NativeStartBudget()
                    fact.instances.append(self)
                def prewarm(self):
                    super().prewarm()  # exactly one canonical Q25 baseline warm
                    self.refiller=Replenishment(self)
                    self.refiller.start()
                    self.last_replenish=time.monotonic()
                    fact.inventory={'initial_native_pairs':len(self.forward.pairs),
                        'scanner_target_pairs':28, 'ready_pairs':len(self.old.READY_TOKENS),
                        'extra_startup_discovery_skipped':True,
                        'readiness_certified_for_28':False,
                        'scope':'NATIVE_BASELINE_PLUS_RATE_BUDGETED_REFILL'}
                    print('[ORACLE380_INITIAL_INVENTORY]',json.dumps(fact.inventory,sort_keys=True),flush=True)
                def controlled_replenish(self,token):
                    if self.refiller is None:raise Hold('REPLENISH_NOT_INITIALIZED')
                    raise Hold(self.refiller.request(token))
                def prepare_unsigned(self,row):
                    if self.refresh_fatal:raise Hold('PREWARM_PARTIAL_MUTATION_FAIL_CLOSED')
                    token=row.get('token')
                    if token not in self.forward.pairs or token not in self.old.READY_TOKENS:
                        self.controlled_replenish(token)
                    if not self.native_budget.admit():
                        raise Hold('NATIVE_RPC_BUDGET_EXHAUSTED_NEEDS_FRESH_EVENT')
                    return super().prepare_unsigned(row)
            return Provider
    return Factory

def diagnostic_worker_factory(m379):
    original=m379.make_scheduling_worker
    def make_worker(legacy_factory,core,native,provider,rpc,accum,metrics):
        legacy=original(legacy_factory,core,native,provider,rpc,accum,metrics)
        class DiagnosticWorker(legacy):
            def loop(self):
                while True:
                    with self.cv:
                        while not self.latest and not self.stop:self.cv.wait(.2)
                        if self.stop:return
                        key=next(iter(self.latest));row,generation=self.latest.pop(key)
                        enqueue=self.enqueued_at.pop(key,time.perf_counter_ns())
                    metrics.timing('queue_ms',(time.perf_counter_ns()-enqueue)/1e6)
                    stage='NOMINATION';reason='NOT_CERTIFIED'
                    result={'stage':'HOLD','reason':reason}
                    try:
                        if self.newer_or_invalid(key,generation):raise native.Hold('SUPERSEDED_BEFORE_NATIVE')
                        issue=core.stage1_nomination(row)
                        if issue:raise native.Hold(issue)
                        stage='NATIVE_PREPARE';t=time.perf_counter_ns()
                        try:proof=provider.prepare_unsigned(row)
                        finally:metrics.timing('native_ms',(time.perf_counter_ns()-t)/1e6)
                        if self.newer_or_invalid(key,generation):raise native.Hold('SUPERSEDED_BEFORE_SIM')
                        stage='SIMULATION';t=time.perf_counter_ns()
                        try:result=core.simulation_gate(row,proof,rpc)
                        finally:metrics.timing('simulation_and_fee_ms',(time.perf_counter_ns()-t)/1e6)
                        stage='POST_SIM'
                        if not isinstance(result,dict) or result.get('stage') not in ('HOLD','UNSIGNED_SIM_NET_ESTIMATE_PASS'):
                            raise native.Hold('SIM_GATE_RESULT_INVALID')
                        if self.newer_or_invalid(key,generation):raise native.Hold('SUPERSEDED_AFTER_SIM')
                    except Exception as exc:
                        diag=error_identity(exc,stage)
                        result={'stage':'HOLD','reason':diag['reason'],'diagnostic':diag}
                        metrics.count('error_stage_'+diag['stage'])
                        if '429' in diag['reason']:metrics.count('rpc_rate_limited_native_no_retry')
                    metrics.timing('queue_to_decision_ms',(time.perf_counter_ns()-enqueue)/1e6)
                    reason=str(result.get('reason') or result.get('stage') or 'UNKNOWN')[:95]
                    metrics.count('decision_'+re.sub('[^A-Za-z0-9_]','_',reason))
                    if result.get('stage')=='UNSIGNED_SIM_NET_ESTIMATE_PASS':
                        metrics.count('unsigned_sim_net_estimate_pass_not_realized_profit')
                    with self.cv:
                        self.results.append(result);self.results=self.results[-80:]
                        self.counts[reason]+=1
                    accum[reason]+=1
                    view={'stage':result.get('stage'),'reason':reason,'direction':row.get('direction'),
                          'size_lamports':row.get('size_lamports'),'event_id':row.get('event_id')}
                    if 'diagnostic' in result:view['diagnostic']=result['diagnostic']
                    print('[ORACLE380_GATE]',json.dumps(view,sort_keys=True),flush=True)
        return DiagnosticWorker
    return make_worker

def install():
    src=Path(__file__).resolve().read_bytes()
    compile(src.decode('utf8'),str(TARGET),'exec')
    if not (ROOT/'oracle_379_five_goal_executor.py').exists():
        raise Hold('ORACLE379C_INSTALLED_BASELINE_REQUIRED')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile('wb',dir=TARGET.parent,delete=False) as f:f.write(src);tmp=f.name
        os.replace(tmp,TARGET)
    print('[ORACLE380_INSTALL_PASS]',str(TARGET),flush=True)

def audit():
    if not TARGET.exists() or TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise Hold('ORACLE380_SOURCE_INTEGRITY_FAILURE')
    m379,m378=import_deps();m379.audit()
    if any((AUTHORITY,SIGNING,BROADCAST)):
        raise Hold('EXECUTION_AUTHORITY_VIOLATION')
    print('[ORACLE380_AUDIT_PASS] ORACLE322_FROZEN ORACLE379_NATIVE_GATES '
        'Q25_SINGLE_STARTUP DISCOVERY_ASYNC_BACKOFF DIRECTION_LANES STAGE_ERRORS NO_KEY_NO_SIGN_NO_BROADCAST',flush=True)

def tests():
    class T(unittest.TestCase):
        def test_retry_after(self):
            class E(Exception):
                code=429;headers={'Retry-After':'12'}
            self.assertEqual(rate_delay(E(),9),12)
        def test_retry_after_clamp(self):
            class E(Exception):headers={'Retry-After':'99999'}
            self.assertEqual(rate_delay(E(),1),300)
        def test_backoff_jitter(self):
            class R:
                def uniform(self,a,b):return 1.
            self.assertEqual(rate_delay(RuntimeError(),3,R()),4)
        def test_http_429(self):
            class E(Exception):code=429
            self.assertTrue(is_429(E()))
        def test_diagnostic_no_raw_url(self):
            e=RuntimeError('RPC crashed https://example.com/?api-key=SUPER_SECRET')
            obj=error_identity(e,'native_prepare')
            self.assertNotIn('SUPER_SECRET',str(obj));self.assertEqual(obj['stage'],'NATIVE_PREPARE')
        def test_diagnostic_staged(self):
            self.assertEqual(error_identity(ValueError('secret'),'SIMULATION')['reason'],'SIMULATION_VALUEERROR')
        def test_no_trading(self):self.assertEqual((AUTHORITY,SIGNING,BROADCAST),(False,False,False))
        def test_canary(self):self.assertEqual(CANARY,10000000)
        def test_timeout_class(self):self.assertEqual(error_identity(TimeoutError(),'RPC')['reason'],'RPC_TIMEOUT')
        def test_pending_request(self):
            class P:pass
            p=P();p.forward=P();p.forward.pairs={};p.old=P();p.old.READY_TOKENS=set()
            c=Replenishment(p,delay=0)
            tok='A'*43
            self.assertEqual(c.request(tok),'REPLENISH_QUEUED_FRESH_EVENT_REQUIRED')
            self.assertEqual(c.request(tok),'REPLENISH_PENDING_FRESH_EVENT_REQUIRED')
            self.assertEqual(c.snapshot()['pending_count'],1)
        def test_short_token_rejected(self):
            class P:pass
            c=Replenishment(P())
            self.assertEqual(c.request('bad'),'REPLENISH_BAD_TOKEN_IDENTITY')
        def test_rate_limit_backoff_no_secret(self):
            class E(Exception):code=429;headers={'Retry-After':'30'}
            class Q:
                def prepare_once(self,root):raise E('key=secret')
            class O:pass
            o=O();o.q25=O();o.q25.q60b2=Q()
            p=O();p.old=o;p.forward=O();p.forward.pairs={}
            c=Replenishment(p,clock=lambda:100.,delay=0)
            c.attempt_once()
            self.assertEqual(c.snapshot()['status'],'HOLD_429_BACKOFF')
            self.assertGreaterEqual(c.next_allowed,130.)
            self.assertNotIn('secret',str(c.snapshot()))
        def test_fresh_after_complete_background_warm(self):
            class Obj:pass
            class Pair:
                def __init__(self,t):self.token=t
            old=Obj();old.READY_TOKENS={'A'};old.q25=Obj()
            pair_a=Pair('A');pair_b=Pair('B')
            old.q25.q60b2=Obj()
            old.q25.q60b2.prepare_once=lambda root:({'pairs':[pair_a,pair_b]},None)
            old.q25.bind_cached_state=lambda state:None
            old.install_proven_hot_math=lambda state:(old.READY_TOKENS.add('B') or [{'token':'A','program':'SPL'},{'token':'B','program':'SPL'}])
            old.prebuild_templates=lambda state,wallet:None
            old.prebuild_meteora_templates=lambda state,wallet,warmed:None
            p=Obj();p.old=old;p.refresh_fatal=False
            p.forward=Obj();p.forward.pairs={'A':pair_a};p.forward.programs={'A':'SPL'}
            p.forward.lock=threading.Lock();p.forward.wallet='WALLET'
            c=Replenishment(p,clock=lambda:100.,delay=0)
            with c.cv:c.pending['B']=100.
            c.attempt_once()
            self.assertIn('B',p.forward.pairs)
            self.assertIn('B',p.old.READY_TOKENS)
            self.assertEqual(c.snapshot()['pending_count'],0)
            self.assertEqual(c.snapshot()['counts']['resolved_requests'],1)
            self.assertEqual(c.snapshot()['status'],'NEW_CANONICAL_PAIRS_WARMED_REQUIRE_NEW_EVENT')
        def test_partial_mutation_fails_closed(self):
            class O:pass
            class Pair:token='B'
            o=O();o.READY_TOKENS={'A'};o.q25=O();o.q25.q60b2=O()
            o.q25.q60b2.prepare_once=lambda root:({'pairs':[O(),Pair()]},None)
            # New discovery would otherwise fail token extraction for O(), prove no publish.
            p=O();p.old=o;p.refresh_fatal=False;p.forward=O();p.forward.pairs={'A':O()}
            c=Replenishment(p,clock=lambda:100.,delay=0)
            c.attempt_once()
            self.assertEqual(set(p.forward.pairs),{'A'})
        def test_native_budget_nonblocking_bounded(self):
            current=[0.]
            b=NativeStartBudget(rate=1,burst=2,clock=lambda:current[0])
            self.assertTrue(b.admit());self.assertTrue(b.admit())
            self.assertFalse(b.admit())
            current[0]=1.
            self.assertTrue(b.admit())
            self.assertEqual(b.snapshot()['native_starts_budget_held'],1)
        def test_native_budget_never_sleeps(self):
            import inspect
            self.assertNotIn('sleep(',inspect.getsource(NativeStartBudget.admit))
        def test_no_restart_hot_callback(self):
            import inspect
            self.assertNotIn('prepare_once(',inspect.getsource(Replenishment.request))
            self.assertNotIn('time.sleep(',inspect.getsource(Replenishment.request))
        def test_provider_preserves_legacy(self):
            import inspect
            text=inspect.getsource(provider_factory)
            self.assertIn('CompatibleNativeProvider',text)
            self.assertIn('super().prepare_unsigned(row)',text)
        def test_no_bypass(self):
            import inspect
            s=inspect.getsource(diagnostic_worker_factory)
            for x in ('stage1_nomination','simulation_gate','newer_or_invalid'):
                self.assertIn(x,s)
        def test_no_live_secret_in_report(self):
            import inspect
            self.assertNotIn('private_key',inspect.getsource(Replenishment.snapshot))
        def test_refill_not_full_28_claim(self):
            import inspect
            self.assertIn('readiness_certified_for_28',inspect.getsource(provider_factory))
        def test_error_source_sanitized(self):
            self.assertEqual(error_identity(Hold('EXACT_CERTIFIED_HOLD'),'native')['reason'],'NATIVE_EXACT_CERTIFIED_HOLD')
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if result.wasSuccessful():print('[ORACLE380_TEST_PASS]',result.testsRun,flush=True);return 0
    return 1

def run(minutes,poll_ms,wallet):
    m379,m378=import_deps()
    audit()
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:raise Hold('RUN_BOUNDS_INVALID')
    Factory=provider_factory(m379,m378)
    orig_factory=m379.InventoryProviderFactory
    orig_worker=m379.make_scheduling_worker
    orig_report=m379.REPORT
    m379.InventoryProviderFactory=Factory
    m379.make_scheduling_worker=diagnostic_worker_factory(m379)
    m379.REPORT=REPORT
    status='HOLD_UNEXPECTED';rc=2
    try:
        rc=m379.run(minutes,poll_ms,wallet)
        status='READ_ONLY_EXECUTOR_SESSION_DONE' if rc==0 else 'READ_ONLY_EXECUTOR_HOLD'
    except Exception as exc:
        status=error_identity(exc,'RUNTIME')['reason']
        rc=2
        print('[ORACLE380_RUNTIME_HOLD]',status,flush=True)
    finally:
        m379.InventoryProviderFactory=orig_factory
        m379.make_scheduling_worker=orig_worker
        m379.REPORT=orig_report
        active=Factory.active
        fill=[]
        if active:
            for instance in active.instances:
                if instance.refiller:
                    instance.refiller.close()
                    snap=instance.refiller.snapshot()
                    snap['native_ready_final']=len(instance.old.READY_TOKENS)
                    snap['native_inventory_final']=len(instance.forward.pairs)
                    snap['native_rpc_budget']=instance.native_budget.snapshot()
                    fill.append(snap)
        obj={}
        if REPORT.exists():
            try:obj=json.loads(REPORT.read_text(encoding='utf8'))
            except (OSError,ValueError):obj={}
        obj.update({'build':'ORACLE380','read_only_session_status':status,'replenishment':fill,
            'realized_profit_certified':False,'execution_authority':False,
            'signing':False,'broadcast':False,'scanner_frozen':True})
        json_write(REPORT,obj)
        print('[ORACLE380_REPORT]',REPORT,flush=True)
        print('[ORACLE380_STATUS]',status,flush=True)
    return rc

def main():
    a=argparse.ArgumentParser()
    for flag in ('install','test','audit','sdk-check','v2-probe','burst','run'):
        a.add_argument('--'+flag,action='store_true')
    a.add_argument('--minutes',type=int,default=5)
    a.add_argument('--poll-ms',type=int,default=5)
    a.add_argument('--wallet-pubkey',default=os.getenv('QSB_SOLANA_WALLET',''))
    x=a.parse_args()
    if not any((x.install,x.test,x.audit,x.sdk_check,x.v2_probe,x.burst,x.run)):
        a.error('SPECIFY_ACTION')
    if x.install:install()
    if x.test:
        rc=tests()
        if rc:return rc
    if x.audit:audit()
    if x.sdk_check:import_deps()[0].sdk_check_visible()
    if x.v2_probe:import_deps()[0].v2_probe()
    if x.burst:print('[ORACLE380_BURST_PASS]',json.dumps(import_deps()[0].burst(),sort_keys=True),flush=True)
    if x.run:return run(x.minutes,x.poll_ms,x.wallet_pubkey)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print('[ORACLE380_HOLD]',error_identity(e,'INSTALL_OR_RUNTIME')['reason'],flush=True)
        sys.exit(2)
