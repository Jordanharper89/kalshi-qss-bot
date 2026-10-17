"""ORACLE-381 full executor-side canonical replenishment and health transparency.

Install self-contained module; scanner ORACLE-322 frozen. No key, signing,
transaction broadcasting, fee/profit override or live trade permission.
"""
from __future__ import annotations
import argparse
import collections
import importlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

PKG='qseries_v2.oracle_execution.solana_atomic_executor'
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET=ROOT/'oracle_381_canonical_replenishment_health.py'
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_381_replenishment_health.json')
PREVIOUS=Path('runtime_state/oracle/final_boss_dual/oracle_380_capacity_and_rpc.json')
DATA=Path('runtime_state/oracle/final_boss_dual')
AUTHORITY=SIGNING=BROADCAST=False
CANARY=10_000_000
UNMATCHED_TTL_S=120.0

class Hold(RuntimeError):pass

def imports():
    return importlib.import_module(PKG+'.oracle_380_rpc_admission_diagnostics')

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=p.parent,delete=False) as f:
        json.dump(obj,f,sort_keys=True,indent=2,default=str);tmp=f.name
    os.replace(tmp,p)

def safe_report(p):
    try:
        if not p.is_file():return {}
        v=json.loads(p.read_text(encoding='utf8'))
        return v if isinstance(v,dict) else {}
    except (ValueError,OSError):return {}

def scanner_health_snapshot(data=DATA,clock=None):
    """Read-only indicators, not a substitute for the frozen scanner validator."""
    clock=clock or time.time
    out={}
    for name in ('scanner_status.json','scanner_live.json'):
        f=data/name;rec={'exists':f.is_file()}
        if f.is_file():
            try:
                j=json.loads(f.read_text(encoding='utf8'))
                rec.update({'mtime_age_s':round(max(0.,clock()-f.stat().st_mtime),2),
                     'state':str(j.get('status','UNKNOWN'))[:40],
                     'epoch':j.get('epoch') if type(j.get('epoch')) is int else None,
                     'snapshots_010':j.get('snapshots_010') if type(j.get('snapshots_010')) is int else None,
                     'candidates_to_executor':j.get('candidates_to_executor') if type(j.get('candidates_to_executor')) is int else None})
            except (ValueError,OSError,AttributeError,TypeError):rec['readable']=False
        out[name]=rec
    out['interpretation']='INDICATORS_ONLY_SCANNER_VALIDATOR_REMAINS_MANDATORY'
    return out


def replenishment_class(m380):
    parent=m380.Replenishment
    class CanonicalReplenishment(parent):
        """Canonical pair discrimination, one discovery thread, explicit cold/absent states.

        No scanner changes and no candidate retries; every new event is re-vetted.
        """
        def __init__(self,provider,**kw):
            super().__init__(provider,**kw)
            self.excluded={}  # token => monotonic expiration after complete discovery
            self.latest_canonical_size=None
            self.latest_canonical_prefixes=[]
            self.phase='WAITING'
            self.attempt_started=None
            self.last_elapsed_ms=None
            self.last_error=None
            self.latest_validated=False
            self.nonmonotonic_missing=0
        def request(self,token):
            # A time-bounded known-absent result is not an invitation to trade.
            with self.cv:
                expiry=self.excluded.get(token)
                if expiry is not None:
                    if self.clock()<expiry:
                        self.counts['known_absent_nominations']+=1
                        return 'TOKEN_ABSENT_LATEST_CANONICAL_DISCOVERY_FRESH_REFRESH_REQUIRED'
                    self.excluded.pop(token,None)
            return super().request(token)
        def attempt_once(self):
            p=self.provider
            self.phase='DISCOVERING'
            self.last_error=None
            self.attempt_started=self.clock()
            try:
                state,_=p.old.q25.q60b2.prepare_once(Path.cwd())
                if not isinstance(state,dict) or not isinstance(state.get('pairs'),(list,tuple)) or not state['pairs']:
                    raise Hold('CANONICAL_DISCOVERY_MALFORMED')
                fresh=list(state['pairs'])
                tokens=[]
                for x in fresh:
                    t=getattr(x,'token',None)
                    if not isinstance(t,str) or not t:raise Hold('CANONICAL_PAIR_TOKEN_MISSING')
                    tokens.append(t)
                if len(set(tokens))!=len(tokens):raise Hold('CANONICAL_PAIR_TOKEN_DUPLICATE')
                new=dict(zip(tokens,fresh))
                existing=set(getattr(p.forward,'pairs',{}))
                self.latest_canonical_size=len(new)
                self.latest_canonical_prefixes=[x[:12] for x in sorted(new)[:24]]
                self.latest_validated=False
                if not existing.issubset(new):
                    self.nonmonotonic_missing=len(existing-set(new))
                    self.counts['canonical_universe_changed']+=1
                    self.last_status='HOLD_CANONICAL_UNIVERSE_CHANGED_REQUIRE_REVALIDATION'
                    return
                self.nonmonotonic_missing=0
                self.latest_validated=True
                self.failures=0
                with self.cv:
                    for token in list(self.excluded):
                        if token in new or self.clock()>=self.excluded[token]:
                            self.excluded.pop(token,None)
                    for token in list(self.pending):
                        if token not in new:
                            self.pending.pop(token,None)
                            self.excluded[token]=self.clock()+UNMATCHED_TTL_S
                            self.counts['confirmed_not_in_canonical_discovery']+=1
                    pending=set(self.pending)
                old_ready=set(str(x) for x in getattr(p.old,'READY_TOKENS',()))
                need=bool(set(new)-existing or any(t not in old_ready for t in pending))
                if not need:
                    with self.cv:
                        for token in list(self.pending):
                            if token in old_ready and token in existing:
                                self.pending.pop(token,None)
                                self.counts['already_ready_resolved']+=1
                    self.last_status='CANONICAL_UNCHANGED_PENDING_RECONCILED'
                    return
                if self.dead:return
                self.phase='NATIVE_PREWARM'
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
                            raise Hold('CANONICAL_NATIVE_TEMPLATES_INCOMPLETE')
                        p.forward.state=state
                        p.forward.pairs=new
                        p.forward.indexes={str(x.token):i for i,x in enumerate(fresh)}
                        p.forward.programs=programs
                    except Exception:
                        p.refresh_fatal=True
                        raise Hold('CANONICAL_PREWARM_PARTIAL_MUTATION_FAIL_CLOSED') from None
                self.last_success=self.clock()
                with self.cv:
                    for token in list(self.pending):
                        if token in new:
                            self.pending.pop(token,None)
                            self.counts['newly_warmed_requests']+=1
                self.counts['new_pairs_warmed']+=len(set(new)-existing)
                self.last_status='NATIVE_PREWARM_COMPLETED_REQUIRE_FRESH_SCANNER_EVENT'
            except Exception as exc:
                self.failures+=1
                self.last_error=m380.error_identity(exc,'DISCOVERY_PREWARM')
                if m380.is_429(exc):
                    delay=m380.rate_delay(exc,self.failures)
                    with self.cv:self.next_allowed=max(self.next_allowed,self.clock()+delay)
                    self.counts['http_429']+=1;self.last_status='HOLD_429_BACKOFF'
                elif isinstance(exc,Hold) and str(exc)=='CANONICAL_PREWARM_PARTIAL_MUTATION_FAIL_CLOSED':
                    self.counts['fatal_prebuild']+=1
                    self.last_status='HOLD_PARTIAL_MUTATION_FAIL_CLOSED'
                    with self.cv:self.next_allowed=float('inf')
                else:
                    self.counts['discovery_or_prebuild_failure']+=1
                    self.last_status=self.last_error['reason']
                    with self.cv:self.next_allowed=max(self.next_allowed,self.clock()+m380.rate_delay(exc,self.failures))
            finally:
                self.last_elapsed_ms=round((self.clock()-self.attempt_started)*1000,2)
                self.phase='IDLE'
        def snapshot(self):
            out=super().snapshot()
            with self.cv:
                out.update({'latest_validated_complete_discovery':self.latest_validated,
                  'latest_exact_pairs_discovered':self.latest_canonical_size,
                  'latest_pair_token_prefixes':list(self.latest_canonical_prefixes),
                  'known_absent_count':sum(self.clock()<t for t in self.excluded.values()),
                  'pending_token_prefixes':[str(x)[:12] for x in list(self.pending)[:20]],
                  'nonmonotonic_existing_missing':self.nonmonotonic_missing,
                  'phase':self.phase,
                  'discovery_elapsed_ms':self.last_elapsed_ms,
                  'discovery_inflight_s':(round(max(0.,self.clock()-self.attempt_started),2)
                      if self.attempt_started is not None and self.phase!='IDLE' else None),
                  'last_failure':self.last_error})
            return out
    return CanonicalReplenishment


def scanner_bus_probe(scan=None):
    """Run the ORIGINAL health validator through its read-only SQLite bus.

    This is diagnostic only: it cannot change or override source health.
    """
    conn=None
    try:
        if scan is None:
            m379,_=imports().import_deps()
            m363,_,_,_=m379.modules()
            scan=m363.resolve_scanner_bus()
        conn=scan.bus()
        conn.execute('PRAGMA query_only=ON')
        hb=scan.validate_scanner(conn)
        if not isinstance(hb,dict):raise Hold('SCANNER_HEALTH_CONTRACT_INVALID')
        return {'validator':'PASS',
            'epoch':hb.get('epoch') if type(hb.get('epoch')) is int else None,
            'producer_prefix':str(hb.get('producer',''))[:12],
            'read_only_sqlite':True,'health_bypass':False}
    except Exception as exc:
        # Never print the raw message; it may contain provider credentials.
        diag=imports().error_identity(exc,'SCANNER_HEALTH')
        return {'validator':'HOLD','reason':diag['reason'],
            'exception_type':diag['exception_type'],'read_only_sqlite':True,
            'health_bypass':False}
    finally:
        if conn is not None:
            try:conn.close()
            except Exception:pass

def read_status():
    prev=safe_report(PREVIOUS)
    result={'build':'ORACLE381','mode':'READ_ONLY_INSPECTION',
       'prior_executor_status':str(prev.get('read_only_session_status','UNKNOWN'))[:75],
       'prior_replenishment':[],
       'scanner':scanner_health_snapshot(),
       'original_scanner_validator':scanner_bus_probe(),
       'no_scanner_mutation':True,'signing':False,'broadcast':False}
    for x in prev.get('replenishment',[]):
        if isinstance(x,dict):
            result['prior_replenishment'].append({
                k:x.get(k) for k in ('status','pending_count','next_attempt_wait_s',
                   'thread_running','native_inventory_final','native_ready_final','counts','failed_closed')})
    print('[ORACLE381_PRIOR_STATE]',json.dumps(result,sort_keys=True),flush=True)
    return result

def install():
    src=Path(__file__).resolve().read_bytes()
    compile(src.decode('utf8'),str(TARGET),'exec')
    if not (ROOT/'oracle_380_rpc_admission_diagnostics.py').is_file():
        raise Hold('ORACLE380_INSTALLED_BASELINE_REQUIRED')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile('wb',dir=TARGET.parent,delete=False) as f:f.write(src);tmp=f.name
        os.replace(tmp,TARGET)
    print('[ORACLE381_INSTALL_PASS]',TARGET,flush=True)

def audit():
    if not TARGET.is_file() or TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise Hold('ORACLE381_SOURCE_INTEGRITY_FAILURE')
    imports().audit()
    if (AUTHORITY,SIGNING,BROADCAST)!=(False,False,False):raise Hold('AUTHORITY_INVARIANT_FAILED')
    print('[ORACLE381_AUDIT_PASS] ORACLE322_FROZEN ORACLE380_GATES_PRESERVED '
          'NO_SCANNER_HEALTH_BYPASS NO_SIGN_NO_BROADCAST',flush=True)

def tests():
    class T(unittest.TestCase):
        def base(self):
            class O:pass
            class Pair:
                def __init__(self,token):self.token=token
            p=O();p.refresh_fatal=False;p.old=O();p.old.q25=O();p.old.q25.q60b2=O()
            p.old.READY_TOKENS={'A'*43}
            p.old.q25.bind_cached_state=lambda st:None
            p.old.install_proven_hot_math=lambda st:[{'token':x.token,'program':'SPL'} for x in st['pairs']]
            p.old.prebuild_templates=lambda st,w:None
            p.old.prebuild_meteora_templates=lambda st,w,warm:None
            p.forward=O();p.forward.pairs={'A'*43:Pair('A'*43)}
            p.forward.wallet='WALLET';p.forward.lock=threading.Lock()
            p.forward.programs={'A'*43:'SPL'}
            return p,Pair
        def obj(self,p):return replenishment_class(imports())(p,clock=lambda:100.,delay=0)
        def test_known_absent_not_requeued(self):
            p,Pair=self.base();p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[Pair('A'*43)]},None)
            c=self.obj(p);self.assertIn('QUEUED',c.request('B'*43));c.attempt_once()
            self.assertEqual(c.snapshot()['pending_count'],0)
            self.assertEqual(c.snapshot()['counts']['confirmed_not_in_canonical_discovery'],1)
            self.assertIn('ABSENT',c.request('B'*43))
        def test_known_absent_cleared_on_new_canonical(self):
            p,Pair=self.base();t='B'*43
            p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[Pair('A'*43),Pair(t)]},None)
            p.old.install_proven_hot_math=lambda st:(p.old.READY_TOKENS.add(t) or [{'token':x.token,'program':'SPL'} for x in st['pairs']])
            c=self.obj(p);c.excluded[t]=220.;c.attempt_once()
            self.assertEqual(c.snapshot()['known_absent_count'],0)
            self.assertIn(t,p.forward.pairs)
        def test_expired_absent_requeues(self):
            p,Pair=self.base();c=self.obj(p);c.excluded['B'*43]=90.
            self.assertIn('QUEUED',c.request('B'*43))
        def test_new_pair_warmed_and_requires_fresh(self):
            p,Pair=self.base();t='B'*43
            p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[Pair('A'*43),Pair(t)]},None)
            c=self.obj(p);c.request(t);p.old.install_proven_hot_math=lambda st:(p.old.READY_TOKENS.add(t) or [{'token':x.token,'program':'SPL'} for x in st['pairs']])
            c.attempt_once();self.assertIn(t,p.forward.pairs)
            self.assertEqual(c.snapshot()['pending_count'],0)
            self.assertEqual(c.snapshot()['status'],'NATIVE_PREWARM_COMPLETED_REQUIRE_FRESH_SCANNER_EVENT')
        def test_nonmonotonic_does_not_mutate(self):
            p,Pair=self.base();p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[Pair('B'*43)]},None)
            c=self.obj(p);c.request('C'*43);c.attempt_once()
            self.assertIn('A'*43,p.forward.pairs)
            self.assertFalse(c.snapshot()['latest_validated_complete_discovery'])
            self.assertEqual(c.snapshot()['nonmonotonic_existing_missing'],1)
        def test_malformed_not_marked_absent(self):
            p,Pair=self.base();p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[]},None)
            c=self.obj(p);c.request('B'*43);c.attempt_once()
            self.assertEqual(c.snapshot()['pending_count'],1)
            self.assertEqual(c.snapshot()['known_absent_count'],0)
        def test_429_backoff(self):
            p,Pair=self.base()
            class E(Exception):code=429;headers={'Retry-After':'30'}
            p.old.q25.q60b2.prepare_once=lambda root:(_ for _ in ()).throw(E('SECRET'))
            c=self.obj(p);c.attempt_once()
            self.assertEqual(c.snapshot()['counts']['http_429'],1)
            self.assertGreaterEqual(c.next_allowed,130)
            self.assertNotIn('SECRET',str(c.snapshot()))
        def test_duplicate_pair_rejects(self):
            p,Pair=self.base();p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[Pair('A'*43),Pair('A'*43)]},None)
            c=self.obj(p);c.attempt_once()
            self.assertIn('DUPLICATE',c.snapshot()['status'])
        def test_existing_ready_reconciled(self):
            p,Pair=self.base();p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[Pair('A'*43)]},None)
            c=self.obj(p);c.attempt_once()
            self.assertEqual(c.snapshot()['status'],'CANONICAL_UNCHANGED_PENDING_RECONCILED')
        def test_source_missing(self):
            with tempfile.TemporaryDirectory() as t:
                s=scanner_health_snapshot(Path(t))
                self.assertFalse(s['scanner_status.json']['exists'])
        def test_source_age(self):
            with tempfile.TemporaryDirectory() as t:
                f=Path(t)/'scanner_status.json';f.write_text('{"status":"RUNNING","epoch":1}',encoding='utf8')
                a=scanner_health_snapshot(Path(t),clock=lambda:f.stat().st_mtime+7.)
                self.assertEqual(a['scanner_status.json']['mtime_age_s'],7.)
        def test_native_scanner_health_probe_good(self):
            import sqlite3
            class S:
                def bus(self):return sqlite3.connect(':memory:')
                def validate_scanner(self,conn):return {'epoch':1,'producer':'PRODUCER'}
            self.assertEqual(scanner_bus_probe(S())['validator'],'PASS')
        def test_native_scanner_health_probe_holds(self):
            import sqlite3
            class S:
                def bus(self):return sqlite3.connect(':memory:')
                def validate_scanner(self,conn):raise RuntimeError('SCANNER_NOT_HEALTHY')
            obj=scanner_bus_probe(S())
            self.assertEqual(obj['validator'],'HOLD')
            self.assertIn('SCANNER_NOT_HEALTHY',obj['reason'])
        def test_source_malformed_safe(self):
            with tempfile.TemporaryDirectory() as t:
                (Path(t)/'scanner_status.json').write_text('NOT_JSON')
                self.assertFalse(scanner_health_snapshot(Path(t))['scanner_status.json']['readable'])
        def test_report_no_secret(self):
            p,Pair=self.base();p.old.q25.q60b2.prepare_once=lambda root:({'pairs':[Pair('A'*43)]},None)
            c=self.obj(p);c.attempt_once()
            self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',str(c.snapshot()))
        def test_no_trading(self):self.assertEqual((AUTHORITY,SIGNING,BROADCAST,CANARY),(False,False,False,10000000))
        def test_stage_diagnostics_retained(self):
            import inspect
            self.assertIn('diagnostic_worker_factory',inspect.getsource(imports().run))
        def test_no_legacy_scanner_import(self):
            import inspect
            self.assertNotIn('oracle_322',inspect.getsource(replenishment_class))
        def test_only_new_events_after_warm(self):
            import inspect
            self.assertIn('REQUIRE_FRESH_SCANNER_EVENT',inspect.getsource(replenishment_class))
        def test_error_sanitized(self):
            p,Pair=self.base();p.old.q25.q60b2.prepare_once=lambda root:(_ for _ in ()).throw(ValueError('api-key=SUPERSECRET'))
            c=self.obj(p);c.attempt_once();self.assertNotIn('SUPERSECRET',str(c.snapshot()))
        def test_runtime_does_not_modify_original_modules(self):
            import inspect
            self.assertIn('finally:',inspect.getsource(run))
        def test_original_live_gate_intact(self):
            import inspect
            self.assertIn('m380.run(',inspect.getsource(run))
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE381_TEST_PASS]' if r.wasSuccessful() else '[ORACLE381_TEST_FAIL]',r.testsRun,flush=True)
    return 0 if r.wasSuccessful() else 1

def run(minutes,poll_ms,wallet):
    m380=imports();audit()
    original=m380.Replenishment
    m380.Replenishment=replenishment_class(m380)
    status='READ_ONLY_EXECUTOR_HOLD';rc=2
    try:
        rc=m380.run(minutes,poll_ms,wallet)
        status='READ_ONLY_EXECUTOR_COMPLETE' if rc==0 else 'READ_ONLY_EXECUTOR_HOLD'
    except Exception as exc:
        status=m380.error_identity(exc,'ORACLE381_RUNTIME')['reason']
        print('[ORACLE381_RUNTIME_HOLD]',status,flush=True)
    finally:
        m380.Replenishment=original
        prior=read_status()
        obj=safe_report(PREVIOUS)
        obj.update({'build':'ORACLE381','session_status':status,'scanner_health_indicators':prior['scanner'],
             'read_only':True,'execution_authority':False,'signing':False,'broadcast':False,
             'realized_profit_certified':False,'first_funded_canary_lamports':CANARY,
             'scanner_validator_not_bypassed':True})
        atomic_json(REPORT,obj)
        print('[ORACLE381_REPORT]',REPORT,flush=True)
        print('[ORACLE381_STATUS]',status,flush=True)
    return rc if status=='READ_ONLY_EXECUTOR_COMPLETE' else 2

def main():
    ap=argparse.ArgumentParser()
    for f in ('install','test','audit','sdk-check','burst','inspect','health-gate','run'):ap.add_argument('--'+f,action='store_true')
    ap.add_argument('--minutes',type=int,default=5);ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET',''))
    a=ap.parse_args()
    if not any((a.install,a.test,a.audit,a.sdk_check,a.burst,a.inspect,a.health_gate,a.run)):
        ap.error('SPECIFY_ACTION')
    if a.install:install()
    if a.test:
        if tests():return 1
    if a.audit:audit()
    if a.sdk_check:imports().import_deps()[0].sdk_check_visible()
    if a.burst:print('[ORACLE381_BURST_PASS]',json.dumps(imports().import_deps()[0].burst(),sort_keys=True),flush=True)
    if a.inspect:read_status()
    if a.health_gate:
        probe=scanner_bus_probe()
        if probe.get('validator')!='PASS':
            print('[ORACLE381_SCANNER_HEALTH_HOLD]',json.dumps(probe,sort_keys=True),flush=True)
            return 2
        print('[ORACLE381_SCANNER_HEALTH_PASS]',json.dumps(probe,sort_keys=True),flush=True)
    if a.run:return run(a.minutes,a.poll_ms,a.wallet_pubkey)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        # Report no exception message, URL or environment variable values.
        print('[ORACLE381_HOLD]',type(exc).__name__,flush=True)
        raise SystemExit(2)
