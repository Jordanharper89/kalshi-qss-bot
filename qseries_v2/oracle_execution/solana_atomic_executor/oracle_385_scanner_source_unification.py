"""ORACLE-385 full replacement installer: one certified scanner source for native launcher.

Read-only structural source-unification over ORACLE-384. No modifications to the
frozen ORACLE-322 scanner, no separate websockets, no signing, no broadcast.
Does not relax the legacy scanner health validator; it selects the already
certified ORACLE-351/363 source used by the canonical event reader.
"""
from __future__ import annotations
import argparse
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
TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_385_scanner_source_unification.py')
REPORT=Path('runtime_state/oracle/final_boss_dual/oracle_385_scanner_source_unification.json')
CANARY=10_000_000
AUTHORITY=SIGNING=BROADCAST=False

class Hold(RuntimeError):pass


def imports():
    m384=importlib.import_module(PKG+'.oracle_384_exact_pool_free_rpc_repair')
    m381=importlib.import_module(PKG+'.oracle_381_canonical_replenishment_health')
    m363=importlib.import_module(PKG+'.oracle_363_verified_scanner_bus_binding')
    m374=importlib.import_module(PKG+'.oracle_374_persistent_dual_native_handoff')
    return m384,m381,m363,m374


def save_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=path.parent,delete=False) as f:
        json.dump(obj,f,indent=2,sort_keys=True);tmp=f.name
    os.replace(tmp,path)


def read_json(path):
    try:return json.loads(Path(path).read_text(encoding='utf8'))
    except (OSError,ValueError,TypeError):return {}


class ReadOnlyScanner:
    """Health checks query the same frozen-certified scanner bus as the event reader."""
    def __init__(self,source):self.source=source
    def bus(self):
        conn=self.source.bus()
        try:
            conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA busy_timeout=500')
            return conn
        except Exception:
            conn.close();raise
    def validate_scanner(self,conn):return self.source.validate_scanner(conn)
    def new_events(self,*args,**kw):return self.source.new_events(*args,**kw)


def certify(legacy_launcher, certified_source, sleep=time.sleep):
    """Two independent unmodified ORACLE-374 health checks; zero grace bypass."""
    source=ReadOnlyScanner(certified_source)
    first=legacy_launcher.read_heartbeat(source)
    sleep(.05)
    second=legacy_launcher.read_heartbeat(source)
    if not all(isinstance(x,dict) for x in (first,second)):
        raise Hold('SOURCE_HEALTH_CONTRACT_INVALID')
    if first.get('producer')!=second.get('producer') or first.get('epoch')!=second.get('epoch'):
        raise Hold('SOURCE_HEALTH_UNSTABLE_EPOCH_OR_PRODUCER')
    if first.get('ok') is not True or second.get('ok') is not True:
        raise Hold('SOURCE_NOT_HEALTHY')
    return {'epoch':int(second['epoch']), 'producer_prefix':second['producer'][:12],
            'health_checks':2, 'age_last_s':round(float(second['age_s']),3),
            'read_only_sqlite':True,'validator_unmodified':True,
            'canonical_bus':'ORACLE363_RESOLVED_ORACLE351_SCANNER',
            'legacy_344_not_used_for_native_health':True}


class SourceAlignment:
    """Replace launcher source resolution for one session, not its health policy."""
    def __init__(self,launcher,scanner_resolver):
        self.launcher=launcher;self.scanner_resolver=scanner_resolver
        self.old=None;self.adapter=None;self.installed=False
    def __enter__(self):
        if self.installed:raise Hold('SOURCE_BRIDGE_DOUBLE_INSTALL')
        self.old=self.launcher.modules
        old_components=self.old()
        if not isinstance(old_components,(tuple,list)) or len(old_components)!=3:
            raise Hold('LAUNCHER_COMPONENT_CONTRACT_CHANGED')
        resolved=self.scanner_resolver()
        if not all(callable(getattr(resolved,x,None)) for x in ('bus','validate_scanner','new_events')):
            raise Hold('CERTIFIED_SCANNER_BUS_API_MISSING')
        self.adapter=ReadOnlyScanner(resolved)
        native,core,_legacy=old_components
        def aligned_modules():return native,core,self.adapter
        self.launcher.modules=aligned_modules
        self.installed=True
        return self
    def __exit__(self,*args):
        if self.installed:
            self.launcher.modules=self.old
            self.installed=False
        self.adapter=None
        return False


def self_check():
    m384,m381,m363,m374=imports()
    source=m363.resolve_scanner_bus()
    # This must remain the same source the certified ORACLE-363 ingress resolves.
    status=m381.scanner_bus_probe(scan=source)
    if status.get('validator')!='PASS':raise Hold('CANONICAL_SCANNER_HEALTH_HOLD')
    proof=certify(m374,source)
    if status.get('epoch')!=proof.get('epoch') or status.get('producer_prefix')!=proof.get('producer_prefix'):
        raise Hold('SCANNER_PROBE_AND_LAUNCHER_SOURCE_DIFFER')
    return proof


def audit():
    if not TARGET.is_file() or TARGET.read_bytes()!=Path(__file__).resolve().read_bytes():
        raise Hold('ORACLE385_INSTALLED_SOURCE_MISMATCH')
    if (AUTHORITY,SIGNING,BROADCAST)!=(False,False,False):raise Hold('EXECUTION_AUTHORITY_CHANGED')
    m384,m381,m363,m374=imports()
    if not (callable(m384.run) and callable(m381.scanner_bus_probe) and
            callable(m363.resolve_scanner_bus) and callable(m374.read_heartbeat)):
        raise Hold('SOURCE_BOUNDARY_CONTRACT_CHANGED')
    m384.audit()
    print('[ORACLE385_AUDIT_PASS] SCANNER322_FROZEN ORACLE363_ORIGINAL_CERTIFIED_SOURCE '
          'ORACLE374_ORIGINAL_HEALTH_POLICY SOURCE_PATCH_SESSION_SCOPED '
          'NO_SIGN_NO_BROADCAST',flush=True)


def install():
    src=Path(__file__).resolve().read_bytes()
    compile(src.decode('utf-8'),str(TARGET),'exec')
    if not (TARGET.parent/'oracle_384_exact_pool_free_rpc_repair.py').is_file():
        raise Hold('ORACLE384_BASELINE_NOT_INSTALLED')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.resolve()!=Path(__file__).resolve():
        with tempfile.NamedTemporaryFile('wb',dir=TARGET.parent,delete=False) as f:
            f.write(src);temp=f.name
        os.replace(temp,TARGET)
    if TARGET.read_bytes()!=src:raise Hold('ORACLE385_INSTALL_BYTES_MISMATCH')
    print('[ORACLE385_INSTALL_PASS]',TARGET,flush=True)


def tests():
    class FakeDb:
        def __init__(self):self.queries=[];self.closed=False
        def execute(self,s):self.queries.append(s);return self
        def close(self):self.closed=True
    class Source:
        def __init__(self):self.opens=[];self.calls=0;self.epoch=1;self.producer='CERTIFIED_SOURCE_0123'
        def bus(self):
            c=FakeDb();self.opens.append(c);return c
        def validate_scanner(self,conn):
            self.calls+=1
            if not any('query_only=ON' in s for s in conn.queries):raise RuntimeError('NOT_READ_ONLY')
            return {'ok':True,'producer':self.producer,'epoch':self.epoch,'age_s':.2}
        def new_events(self,*args,**kw):return []
    class Launcher:
        def __init__(self):
            self.calls=0;self.legacy=Source()
            self.modules=lambda:('native','core',self.legacy)
        def read_heartbeat(self,scan):
            self.calls+=1;c=scan.bus()
            try:
                h=scan.validate_scanner(c)
                if h.get('ok') is not True or h.get('age_s',20)>=15:raise RuntimeError('HOLD')
                return h
            finally:c.close()
    class T(unittest.TestCase):
        def test_canary(self):self.assertEqual(CANARY,10000000)
        def test_no_authority(self):self.assertEqual((AUTHORITY,SIGNING,BROADCAST),(False,False,False))
        def test_reader_query_only(self):
            s=Source();db=ReadOnlyScanner(s).bus()
            self.assertTrue(any('query_only=ON' in q for q in db.queries))
            self.assertTrue(any('busy_timeout=500' in q for q in db.queries));db.close()
        def test_twice_health(self):
            l=Launcher();s=Source();p=certify(l,s,sleep=lambda _:None)
            self.assertEqual(p['health_checks'],2);self.assertEqual(s.calls,2)
        def test_source_not_legacy(self):
            l=Launcher();s=Source();orig=l.modules
            with SourceAlignment(l,lambda:s):
                self.assertIs(l.modules()[2].source,s)
                self.assertIsNot(l.modules()[2].source,l.legacy)
                certify(l,l.modules()[2].source,sleep=lambda _:None)
            self.assertIs(l.modules,orig)
        def test_patch_restores_exception(self):
            l=Launcher();orig=l.modules
            with self.assertRaises(ValueError):
                with SourceAlignment(l,Source):raise ValueError('fixture')
            self.assertIs(l.modules,orig)
        def test_double_enter_rejected(self):
            l=Launcher();bridge=SourceAlignment(l,Source)
            with bridge:
                with self.assertRaises(Hold):bridge.__enter__()
        def test_missing_api_rejected(self):
            l=Launcher();orig=l.modules
            with self.assertRaises(Hold):SourceAlignment(l,lambda:object()).__enter__()
            self.assertIs(l.modules,orig)
        def test_health_failure_closed(self):
            l=Launcher();s=Source()
            def bad(_):raise RuntimeError('SCANNER_NOT_HEALTHY')
            s.validate_scanner=bad
            with self.assertRaises(RuntimeError):certify(l,s,sleep=lambda _:None)
        def test_epoch_switch_closed(self):
            l=Launcher();s=Source();old=s.validate_scanner
            def switched(conn):
                h=old(conn);s.epoch=2;return h
            s.validate_scanner=switched
            with self.assertRaises(Hold):certify(l,s,sleep=lambda _:None)
        def test_producer_switch_closed(self):
            l=Launcher();s=Source();old=s.validate_scanner
            def switched(conn):
                h=old(conn);s.producer='OTHER_PRODUCER_0123';return h
            s.validate_scanner=switched
            with self.assertRaises(Hold):certify(l,s,sleep=lambda _:None)
        def test_no_new_ws(self):
            import inspect
            s=inspect.getsource(SourceAlignment)
            self.assertNotIn('websocket',s.lower())
        def test_no_execution(self):
            import inspect
            s=inspect.getsource(run)
            self.assertNotIn('sendTransaction',s)
            self.assertNotIn('sign_transaction',s)
        def test_not_mock_validator(self):
            import inspect
            self.assertIn('self.source.validate_scanner',inspect.getsource(ReadOnlyScanner))
        def test_snapshot_without_secrets(self):
            o=certify(Launcher(),Source(),sleep=lambda _:None)
            self.assertNotIn('private',json.dumps(o).lower())
    rc=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    print('[ORACLE385_TEST_PASS]' if rc.wasSuccessful() else '[ORACLE385_TEST_FAIL]',rc.testsRun,flush=True)
    return 0 if rc.wasSuccessful() else 1


def run(minutes,poll_ms,wallet):
    if not 1<=minutes<=60 or not 5<=poll_ms<=100:raise Hold('RUNTIME_BOUNDS_INVALID')
    m384,m381,m363,m374=imports()
    audit()
    status='READ_ONLY_HOLD';code=2;proof={};start=time.monotonic()
    # Nothing is warmed until both scanner validations certify one unchanged source.
    try:
        source=m363.resolve_scanner_bus()
        original=m381.scanner_bus_probe(scan=source)
        if original.get('validator')!='PASS':raise Hold('SCANNER_HEALTH_GATE_FAILED')
        with SourceAlignment(m374,lambda:source):
            proof=certify(m374,source)
            if original.get('epoch')!=proof['epoch'] or original.get('producer_prefix')!=proof['producer_prefix']:
                raise Hold('SCANNER_SOURCE_PRECHECK_DIFFERENCE')
            print('[ORACLE385_UNIFIED_SOURCE_PASS]',json.dumps(proof,sort_keys=True),flush=True)
            code=m384.run(minutes,poll_ms,wallet)
        status='READ_ONLY_SESSION_DONE' if code==0 else 'READ_ONLY_HOLD'
    finally:
        old=read_json(Path('runtime_state/oracle/final_boss_dual/oracle_384_exact_pool_free_rpc_report.json'))
        output={'build':'ORACLE385','status':status,'duration_s':round(time.monotonic()-start,2),
                'source_certification':proof,'upstream_status':old.get('status'),
                'upstream_native_pairs':old.get('native_pairs_final'),
                'upstream_sdk_ready_pools':old.get('sdk_ready_pools'),
                'execution_authority':False,'private_key_used':False,'signing':False,
                'broadcast':False,'canary_lamports':CANARY,'scanner_mutated':False,
                'native_profit_certified':False}
        save_json(REPORT,output)
        print('[ORACLE385_REPORT]',REPORT,flush=True)
        print('[ORACLE385_STATUS]',status,flush=True)
    return code


def main():
    ap=argparse.ArgumentParser()
    for x in ('install','test','audit','health-gate','node-check','sdk-check','burst','inspect','run'):
        ap.add_argument('--'+x,action='store_true')
    ap.add_argument('--minutes',type=int,default=5)
    ap.add_argument('--poll-ms',type=int,default=5)
    ap.add_argument('--wallet-pubkey',default=os.environ.get('QSB_SOLANA_WALLET',''))
    a=ap.parse_args()
    if not any(getattr(a,x.replace('-','_')) for x in ('install','test','audit','health-gate','node-check','sdk-check','burst','inspect','run')):ap.error('ACTION_REQUIRED')
    if a.install:install()
    if a.test and tests():return 1
    if a.audit:audit()
    if a.health_gate:
        try:print('[ORACLE385_HEALTH_GATE_PASS]',json.dumps(self_check(),sort_keys=True),flush=True)
        except Exception as exc:
            print('[ORACLE385_HEALTH_GATE_HOLD]',type(exc).__name__,flush=True);return 2
    if a.node_check:imports()[0].modules()[0].node_check()
    if a.sdk_check:imports()[0].modules()[0].deps().dep().imports().import_deps()[0].sdk_check_visible()
    if a.burst:print('[ORACLE385_BURST_PASS]',json.dumps(imports()[0].modules()[0].deps().dep().imports().import_deps()[0].burst(),sort_keys=True),flush=True)
    if a.inspect:
        print('[ORACLE385_INSPECT]',json.dumps(read_json(REPORT),sort_keys=True),flush=True)
    if a.run:return run(a.minutes,a.poll_ms,a.wallet_pubkey)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        # No raw messages or exception tracebacks that may contain RPC credentials.
        print('[ORACLE385_HOLD]',type(exc).__name__,flush=True)
        raise SystemExit(2)
