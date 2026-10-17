from __future__ import annotations
"""V11 complete native warm bridge installer. Existing files are never patched or overwritten.

Install only the new V11 module; preserve ORACLE-322, ORACLE-402 and V5-V10.
"""
import argparse,hashlib,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
DEST=PACKAGE/'final_boss_v11_native_bridge.py'
SOURCE=r'''
from __future__ import annotations
"""V11: scoped V8/V10 staging -> existing ORACLE-370/378 native warm -> V9 live source gate.

The existing scanner remains the only market-data producer. This module neither
changes its subscriptions nor inserts synthetic SQLite events. No broadcast code.
Native overrides are in this process only, restored even on failure.
"""
import argparse
import contextlib
import hashlib
import importlib
import json
import os
import re
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'runtime_state/oracle/final_boss_dual'
STAGE = BASE / 'staged_discovery.json'
STAGE_REPORT = BASE / 'final_boss_v10_admission_stage.json'
OUT = BASE / 'final_boss_v11_native_bridge.json'
V9_OUTPUT = BASE / 'final_boss_v9_simulation_gate.json'
PKG = 'qseries_v2.oracle_execution.solana_atomic_executor.'
ADDR = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
V8_SHA = '41633453164b37e5343707e7c43707bdb762280fb57341cbd441e77431ab0bb3'
V9_SHA = '2d17b83e68d554320e993357b2037123d69c1b63341e41043e482d854d0b1e9f'
V10_SHA = '3ad2b3d9a6ef9d0fb66f924a8d27a2b0d5e3974a2476bd8468a27d4c1b56df4f'
WALLET = '7t4krNuD6e6srbZZh2pkMELy1mJSHFTM7HitbBm7vaBE'

class Hold(RuntimeError):
    pass


def code(exc):
    if isinstance(exc, Hold) and re.fullmatch(r'[A-Z][A-Z0-9_]{2,95}', str(exc)):
        return str(exc)
    return type(exc).__name__.upper()


def mod(name):
    return importlib.import_module(PKG + name)


def sha(path):
    if not path.is_file() or path.is_symlink():
        raise Hold('TRUSTED_MODULE_MISSING_OR_LINKED')
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def verify_modules():
    p = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor'
    for name, expect in [('final_boss_mriya_crossvenue_discovery', V8_SHA),
                         ('final_boss_v9_atomic_simulation_gate', V9_SHA),
                         ('final_boss_v10_admission_stage', V10_SHA)]:
        if sha(p / (name + '.py')) != expect:
            raise Hold('TRUSTED_MODULE_SHA_DRIFT_' + name.upper()[:40])
    contract = mod('final_boss_v10_admission_stage').scanner_contract()
    if not contract.get('staged_reader') or contract.get('running_subscription_reload') is not False:
        raise Hold('ORACLE322_STAGING_CONTRACT_DRIFT')
    return contract


def json_doc(path, limit=500000):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        raise Hold('TRUSTED_FILE_MISSING_LINKED_OR_OVERSIZE')
    try:
        x = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        raise Hold('TRUSTED_FILE_INVALID_JSON') from None
    if not isinstance(x, dict):
        raise Hold('TRUSTED_FILE_NOT_OBJECT')
    return x


def triple(row):
    if not isinstance(row, dict):
        raise Hold('STAGED_ROW_NOT_OBJECT')
    t = tuple(row.get(k) for k in ('token', 'pump_pool', 'meteora_pool'))
    if not all(isinstance(v, str) and ADDR.fullmatch(v) for v in t) or len(set(t)) != 3:
        raise Hold('STAGED_EXACT_TRIPLE_INVALID')
    return t


def staged_provenance(now=None, stage_file=STAGE, report_file=STAGE_REPORT, v9=None, v10=None):
    """Require that current live V8 certificate is exactly represented in V10's saved feed."""
    now = time.time() if now is None else now
    v9 = mod('final_boss_v9_atomic_simulation_gate') if v9 is None else v9
    v10 = mod('final_boss_v10_admission_stage') if v10 is None else v10
    source = v9.load_v8(now)
    selected, alternatives, _ = v10.select_v8(source, v9)
    allowed = {triple(r) for r in selected}
    if not allowed or len(allowed) > 28:
        raise Hold('V8_SELECTION_EMPTY_OR_EXCEEDS_CAP')
    stage = json_doc(stage_file)
    ts = stage.get('generated_at')
    if type(ts) not in (int, float) or not 0 <= now-ts <= 600:
        raise Hold('V10_STAGE_EXPIRED')
    rows = stage.get('rows')
    if not isinstance(rows, list) or len(rows) > 112:
        raise Hold('V10_STAGED_ROWS_INVALID')
    mriya = [r for r in rows if isinstance(r, dict)
             and r.get('source') == 'MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW']
    actual = {triple(r) for r in mriya}
    if len(mriya) != len(actual) or actual != allowed:
        raise Hold('V10_STAGED_MRIYA_NOT_EQUAL_FRESH_V8')
    report = json_doc(report_file)
    if report.get('status') != 'STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE' or report.get('stage_written') is not True:
        raise Hold('V10_STAGE_REPORT_NOT_COMMITTED')
    expected_tokens = {t[0] for t in allowed}
    if set(report.get('staged_tokens', [])) != expected_tokens:
        raise Hold('V10_STAGED_TOKEN_PROVENANCE_MISMATCH')
    if not isinstance(report.get('scanner'), dict) or type(report['scanner'].get('epoch')) is not int:
        raise Hold('V10_SCANNER_EPOCH_PROVENANCE_MISSING')
    if stage_file.stat().st_mtime < report_file.stat().st_mtime - 5:
        raise Hold('V10_STAGE_OLDER_THAN_REPORT')
    return {'selected_rows': selected, 'triples': allowed, 'stage_age_s': round(now-ts, 2),
            'stage_epoch': report['scanner']['epoch'],
            'stage_producer_prefix': str(report['scanner'].get('producer_prefix', '')),
            'alternatives_not_promoted': alternatives}


@contextlib.contextmanager
def discovery_override(engine, rows):
    """Inject exact V8 candidates at the front of ORIGINAL discovery, only in this process.

    Does not modify the engine file, the scanner's other process, or its subscriptions.
    Rejects source recursion/repeated injection and restores original on every path.
    """
    original = engine.raw_candidate_universe
    if not callable(original):
        raise Hold('NATIVE_ENGINE_DISCOVERY_INTERFACE_MISSING')
    wanted = [dict(r) for r in rows]
    selected = {triple(r) for r in wanted}
    if len(selected) != len(wanted):
        raise Hold('DUPLICATE_V8_ROWS_IN_OVERRRIDE')
    calls = {'count': 0, 'staged_seen': 0, 'original_seen': 0}

    def merged(root):
        calls['count'] += 1
        if calls['count'] > 3:
            raise Hold('NATIVE_DISCOVERY_UNEXPECTED_RECURSION')
        original_rows = original(root)
        if not isinstance(original_rows, (list, tuple)) or len(original_rows) > 1500:
            raise Hold('NATIVE_DISCOVERY_SOURCE_NOT_BOUNDED_LIST')
        seen_tokens = {r['token'] for r in wanted}
        kept = []
        for row in original_rows:
            if not isinstance(row, dict):
                continue
            if row.get('token') in seen_tokens:
                # A stale source may refer to different pools. Never let it replace V8 identity.
                continue
            kept.append(row)
        calls['staged_seen'] = len(wanted)
        calls['original_seen'] = len(kept)
        # Keep V8 exact rows *first*; normal native 28-slot capacity still applies.
        return [dict(r) for r in wanted] + kept

    engine.raw_candidate_universe = merged
    try:
        yield calls
    finally:
        engine.raw_candidate_universe = original


def stage_advanced(scan, info):
    conn = scan.bus()
    try:
        conn.execute('PRAGMA query_only=ON')
        cur = scan.validate_scanner(conn)
    finally:
        conn.close()
    if cur.get('ok') is not True:
        raise Hold('CANONICAL_SCANNER_HEALTH_INVALID')
    epoch = cur.get('epoch')
    producer = str(cur.get('producer', ''))
    if type(epoch) is not int or not producer:
        raise Hold('SCANNER_EPOCH_OR_PRODUCER_INVALID')
    changed = epoch > info['stage_epoch'] or (epoch >= info['stage_epoch']
              and producer[:12] != info['stage_producer_prefix'] and len(info['stage_producer_prefix']) == 12)
    return {'epoch': epoch, 'producer_prefix': producer[:12], 'after_stage': bool(changed)}


def save(out):
    BASE.mkdir(parents=True, exist_ok=True)
    # No URL, signer, transaction, signature, or other secrets written to disk.
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=BASE, suffix='.tmp', delete=False) as f:
        json.dump(out, f, sort_keys=True, indent=2)
        tmp = Path(f.name)
    try:
        os.replace(tmp, OUT)
    finally:
        tmp.unlink(missing_ok=True)


def run(mode, seconds=90, signed_sim=False, wallet=WALLET):
    out = {'build': 'FINAL_BOSS_V11', 'mode': mode.upper(), 'status': 'HOLD',
           'scanner_modified': False, 'new_websockets': 0, 'canonical_bus_writes': 0,
           'signing': False, 'broadcast': False, 'funded_execution_authority': False,
           'protected_min_out_certified': False, 'simulated_sizes': [],
           'allowed_size_grid_lamports': list(range(10_000_000, 100_000_001, 5_000_000))}
    try:
        if not isinstance(wallet, str) or not ADDR.fullmatch(wallet):
            raise Hold('WALLET_PUBLIC_ADDRESS_INVALID')
        if not 1 <= seconds <= 300:
            raise Hold('OBSERVATION_SECONDS_INVALID')
        if signed_sim and mode != 'observe':
            raise Hold('SIMULATION_ONLY_SUPPORTED_IN_OBSERVE_MODE')
        verify_modules()
        info = staged_provenance()
        out.update(v8_selected_tokens=len(info['selected_rows']),
                   v8_verified_routes=len(info['triples']),
                   stage_age_s=info['stage_age_s'], stage_epoch=info['stage_epoch'])
        scan = mod('oracle_344_scanner_align')
        state = stage_advanced(scan, info)
        out['scanner'] = state
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
        owner = mod('oracle_402_source_first_handoff')
        if not callable(getattr(owner, 'native_inventory', None)) or not callable(getattr(owner, 'native_capacity_scope', None)):
            raise Hold('ORACLE402_NATIVE_INTERFACE_NOT_AVAILABLE')
        with discovery_override(engine, info['selected_rows']) as evidence:
            if mode == 'probe':
                native = mod('oracle_370_native_atomic_executor')
                reverse = mod('oracle_378_native_reverse_atomic')
                with owner.native_capacity_scope():
                    provider = reverse.CompatibleNativeProvider(native, wallet)
                    provider.prewarm()  # Existing original native Q25 warm only; no new WS
                inv = owner.native_inventory(provider)
                actual = set(inv['triples'].values())
                overlap = info['triples'] & actual
                out.update(native_ready=len(inv['ready']), native_exact_triples=len(actual),
                           v8_native_ready_overlap=len(overlap), native_discovery_calls=evidence['count'],
                           native_discovery_rows=evidence['original_seen'],
                           matching_native_routes=[{'token': t, 'pump_pool': p, 'meteora_pool': d}
                                                   for t, p, d in sorted(overlap)])
                if evidence['count'] == 0:
                    raise Hold('NATIVE_PREWARM_DID_NOT_CONSUME_ENGINE_DISCOVERY')
                if not overlap:
                    raise Hold('NATIVE_PREWARM_DID_NOT_HYDRATE_STAGED_V8_ROUTE')
                out['status'] = ('NATIVE_V8_READY_WAITING_FOR_SCANNER_EPOCH'
                                 if not state['after_stage'] else 'NATIVE_V8_READY_NEXT_EPOCH_EVENT_PENDING')
            elif mode == 'observe':
                if not state['after_stage']:
                    raise Hold('SCANNER_STILL_ON_PRESTAGE_EPOCH')
                # V9 reuses its ORIGINAL single scanner-bus reader and original native executor.
                # The only scoped change is which independently verified tokens native warm sees.
                v9 = mod('final_boss_v9_atomic_simulation_gate')
                result = v9.observe(seconds, wallet, signed_sim)
                rep = json_doc(V9_OUTPUT)
                out.update(v9_status=str(rep.get('status'))[:100],
                           v8_native_ready_overlap=rep.get('v8_native_ready_overlap'),
                           matching_events=rep.get('matching_events'),
                           native_unsigned=rep.get('native_unsigned'),
                           signed_simulations=rep.get('signed_simulations'),
                           simulated_sizes=rep.get('sizes_actually_simulated', []),
                           native_discovery_calls=evidence['count'],
                           signing=bool(rep.get('simulation_transaction_signed', False)),
                           simulated_best_size_lamports=rep.get('best_size_lamports'))
                if evidence['count'] == 0:
                    raise Hold('V9_NATIVE_WARM_DID_NOT_CONSUME_DISCOVERY')
                out['status'] = ('SIM_RESULT_RECORDED_NO_BROADCAST' if result == 0 and rep.get('signed_simulations', 0)
                                 else 'HOLD_' + (str(rep.get('status', 'V9_NO_SIMULATION')).removeprefix('HOLD_')[:80]))
            else:
                raise Hold('UNKNOWN_MODE')
    except Exception as exc:
        out['status'] = 'HOLD_' + code(exc)
    finally:
        try:
            save(out)
        except OSError:
            pass
        print('[FINAL_BOSS_V11_NATIVE_BRIDGE]', json.dumps(out, sort_keys=True), flush=True)
        print('[REPORT]', OUT.relative_to(ROOT), flush=True)
    return 0 if out['status'].startswith(('NATIVE_V8_READY_', 'SIM_RESULT_RECORDED_')) else 2


def tests():
    from types import SimpleNamespace
    from unittest.mock import patch
    a, b, c, d, e = ('a'*40, 'b'*40, 'c'*40, 'd'*40, 'e'*40)
    rows = [dict(token=a, pump_pool=b, meteora_pool=c, source='MRIYA_V8_NATIVE_VERIFIED_SIM_REVIEW')]
    fake_engine = SimpleNamespace(raw_candidate_universe=lambda root: [
        dict(token=a, pump_pool=b, meteora_pool=d), dict(token=e, pump_pool=b, meteora_pool=d)])
    before = fake_engine.raw_candidate_universe
    with discovery_override(fake_engine, rows) as calls:
        returned = fake_engine.raw_candidate_universe('root')
        assert [triple(z) for z in returned] == [(a,b,c), (e,b,d)]
        assert calls == {'count':1,'staged_seen':1,'original_seen':1}
    assert fake_engine.raw_candidate_universe is before
    try:
        with discovery_override(fake_engine, rows):
            raise ArithmeticError('fixture')
    except ArithmeticError:
        assert fake_engine.raw_candidate_universe is before
    else:
        raise AssertionError('override exception not propagated')
    now=1000.
    stage = {'generated_at':now-20,'rows':[dict(rows[0])]+[dict(token=e,pump_pool=b,meteora_pool=d,source='UNIVERSAL')]}
    report = {'status':'STAGED_FOR_NEXT_SCANNER_EPOCH_NOT_LIVE','stage_written':True,
              'staged_tokens':[a], 'scanner':{'epoch':1,'producer_prefix':'abcdefghijkl'}}
    class V9:
        @staticmethod
        def load_v8(now):return {'prospects':[]}
    class V10:
        @staticmethod
        def select_v8(r,v9):return rows,0,{}
    with tempfile.TemporaryDirectory() as folder:
        sf=Path(folder)/'staged.json';rf=Path(folder)/'report.json'
        sf.write_text(json.dumps(stage));rf.write_text(json.dumps(report))
        p=staged_provenance(now,sf,rf,V9,V10)
        assert p['triples']=={(a,b,c)} and p['stage_epoch']==1
        stage['generated_at']=now-601;sf.write_text(json.dumps(stage))
        try:staged_provenance(now,sf,rf,V9,V10)
        except Hold as ex:assert str(ex)=='V10_STAGE_EXPIRED'
        else:raise AssertionError('stale staged feed accepted')
        stage['generated_at']=now-20;stage['rows'][0]['meteora_pool']=d;sf.write_text(json.dumps(stage))
        try:staged_provenance(now,sf,rf,V9,V10)
        except Hold as ex:assert str(ex)=='V10_STAGED_MRIYA_NOT_EQUAL_FRESH_V8'
        else:raise AssertionError('substituted DLMM accepted')
    class Conn:
        def execute(self, cmd):pass
        def close(self):pass
    class Scan:
        @staticmethod
        def bus():return Conn()
        @staticmethod
        def validate_scanner(conn):return {'ok':True,'epoch':1,'producer':'abcdefghijkl99999'}
    assert not stage_advanced(Scan,{'stage_epoch':1,'stage_producer_prefix':'abcdefghijkl'})['after_stage']
    with patch.object(Scan,'validate_scanner',return_value={'ok':True,'epoch':1,'producer':'zyxwvutsrqpo99999'}):
        assert stage_advanced(Scan,{'stage_epoch':1,'stage_producer_prefix':'abcdefghijkl'})['after_stage']
    assert len(range(10_000_000,100_000_001,5_000_000))==19
    for forbidden in ('send'+'Transaction', 'send'+'RawTransaction', 'accountSubscribe', 'accountUnsubscribe'):
        assert forbidden not in run.__code__.co_names
    print('[PASS] FINAL_BOSS_V11 V8/V10 exact stage, process-scoped native discovery, identity matching, epoch guard, 19 sizes, restored hooks')
    print('[SCOPE] deterministic tests; scanner untouched, no socket, no bus writes, no trade broadcast')


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--test', action='store_true')
    mode.add_argument('--probe', action='store_true')
    mode.add_argument('--observe', action='store_true')
    p.add_argument('--seconds', type=int, default=90)
    p.add_argument('--signed-sim', action='store_true')
    p.add_argument('--wallet', default=os.environ.get('QSB_SOLANA_WALLET', WALLET))
    a = p.parse_args()
    if a.test:
        tests();return 0
    return run('probe' if a.probe else 'observe', a.seconds, a.signed_sim, a.wallet)

if __name__ == '__main__':
    raise SystemExit(main())

'''

def checksum(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()

def install():
    raw=SOURCE.encode('utf-8')
    compile(SOURCE,'final_boss_v11_native_bridge.py','exec')
    PACKAGE.mkdir(parents=True,exist_ok=True)
    if DEST.exists():
        if DEST.is_symlink() or checksum(DEST.read_bytes())!=checksum(raw):
            raise RuntimeError('HOLD_V11_UNKNOWN_EXISTING_MODULE_NO_OVERWRITE')
        print('[PASS] V11_ALREADY_INSTALLED');return
    with tempfile.NamedTemporaryFile('wb',dir=PACKAGE,suffix='.tmp',delete=False) as f:
        f.write(raw);tmp=Path(f.name)
    try:os.replace(tmp,DEST)
    finally:tmp.unlink(missing_ok=True)
    if checksum(DEST.read_bytes())!=checksum(raw):raise RuntimeError('V11_INSTALL_READBACK_MISMATCH')
    print('[INSTALLED]',DEST.relative_to(ROOT))
    print('[SHA256]',checksum(raw))
    print('[PRESERVED] ORACLE-322, Q18/Q20/Q25, original WebSocket, ORACLE-402, V5/V8/V9/V10')
    print('[SCOPE] scoped in-process native discovery; no scanner rotation; no broadcast')

def test():
    compile(SOURCE,'final_boss_v11_native_bridge.py','exec')
    with tempfile.TemporaryDirectory() as d:
        module=Path(d)/'qseries_v2/oracle_execution/solana_atomic_executor/final_boss_v11_native_bridge.py'
        module.parent.mkdir(parents=True,exist_ok=True)
        module.write_text(SOURCE,encoding='utf-8')
        r=subprocess.run([sys.executable,str(module),'--test'],capture_output=True,text=True,timeout=45)
        if r.returncode or '[PASS] FINAL_BOSS_V11' not in r.stdout:
            raise RuntimeError('V11_DETERMINISTIC_TEST_FAILED_'+r.stderr[-250:])
        if checksum(module.read_bytes())!=checksum(SOURCE.encode()):raise RuntimeError('V11_TEST_SOURCE_DRIFT')
    for bad in ('send'+'Transaction(', 'send'+'RawTransaction(', 'accountSubscribe(', 'accountUnsubscribe('):
        if bad in SOURCE:raise RuntimeError('V11_FORBIDDEN_RUNTIME_OPERATION')
    print('[PASS] V11_INSTALLER native scoped bridge, full module tests, no scanner patch or fake events')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--install',action='store_true')
    a=p.parse_args()
    if not(a.test or a.install):p.error('specify --test or --install')
    if a.test:test()
    if a.install:install()
if __name__=='__main__':main()
