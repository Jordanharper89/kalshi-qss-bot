from __future__ import annotations
"""Complete full-file replacement of the ORACLE-402 executor startup.
No scanner or existing native SDK source is modified.
"""
import argparse, hashlib, os, py_compile, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/oracle_402_source_first_handoff.py'
# SHA256 of original ORACLE-402 installed MODULE, normalized to LF.
OLD_SHA = '959713eb460a02d2c2b07159007dbc976e2f9ecd2b37c49714cd4d1a200267f2'
SOURCE = r'''from __future__ import annotations
"""Canonical Final Boss executor startup. Read-only admission; no signer or broadcast."""
import argparse, collections, contextlib, importlib, json, os, re, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
REPORT = ROOT / 'runtime_state/oracle/final_boss_dual/oracle_402_source_first_handoff.json'
GRID = set(range(10_000_000, 100_000_001, 5_000_000))
WALLET_RE = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
class Hold(RuntimeError): pass

def mod(name): return importlib.import_module(PKG + '.' + name)
def safe(exc):
    s = str(exc)
    return s if re.fullmatch(r'[A-Z][A-Z0-9_]{3,90}', s) else type(exc).__name__.upper()

def freeze():
    x = mod('oracle_399_final_boss_execution_owner').source_hashes()
    if len(x) != 4: raise Hold('SCANNER_FREEZE_NOT_COMPLETE')
    return 4

@contextlib.contextmanager
def native_capacity_scope():
    """Only this executor process, only during native startup. Restore without exception."""
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine, live_account_stream as stream
    old = (stream.MAX_PAIRS, engine.MAX_TOKENS)
    previous = {k: os.environ.get(k) for k in ('QARB_HOT_PAIRS', 'QARB_MAX_TOKENS')}
    try:
        stream.MAX_PAIRS = engine.MAX_TOKENS = 28
        os.environ['QARB_HOT_PAIRS'] = os.environ['QARB_MAX_TOKENS'] = '28'
        yield {'before_max_pairs':old[0], 'before_max_tokens':old[1], 'native_only_limit':28}
    finally:
        stream.MAX_PAIRS, engine.MAX_TOKENS = old
        for k, val in previous.items():
            if val is None: os.environ.pop(k, None)
            else: os.environ[k] = val

def scanner_status(hb):
    base = ROOT / 'runtime_state/oracle/final_boss_dual'
    for name in ('scanner_status.json', 'scanner_live.json'):
        p = base / name
        try:
            stat = p.stat(); x = json.loads(p.read_text(encoding='utf-8'))
            if (not isinstance(x, dict) or time.time()-stat.st_mtime > 20
                    or x.get('epoch') != hb['epoch'] or x.get('status',x.get('state')) != 'RUNNING'):
                continue
            n = x.get('admitted')
            if type(n) is int and 0 <= n <= 28:
                return {'admitted':n,'source':name,'epoch':hb['epoch']}
        except (OSError,ValueError,TypeError,KeyError): pass
    raise Hold('SCANNER_CURRENT_ADMITTED_COUNT_UNAVAILABLE')

def native_inventory(provider):
    old = getattr(provider, 'old', None)
    forward = getattr(provider, 'forward', None)
    pairs = getattr(forward, 'pairs', {})
    if not isinstance(pairs, dict): raise Hold('NATIVE_PAIR_REGISTRY_NOT_MAPPING')
    ready = set(map(str, getattr(old, 'READY_TOKENS', ())))
    pump = set(map(str, getattr(old, 'TEMPLATES', {})))
    dlmm = set(map(str, getattr(old, 'METEORA_TEMPLATES', {})))
    programs = set(map(str, getattr(forward, 'programs', {})))
    native = set(map(str, pairs))
    executable = native & ready & pump & dlmm & programs
    return {'native_pairs':len(native),'ready_tokens':len(ready & native),
            'pump_templates':len(pump & native),'meteora_templates':len(dlmm & native),
            'token_programs':len(programs & native), 'both_template_ready':len(executable),
            'missing_native_readiness':[t[:12] for t in sorted(native-executable)[:10]],
            'registered':native, 'ready':executable, 'pairs':pairs}

def candidate_match(row, inventory):
    token = row.get('token')
    if (row.get('schema') != 'ORACLE363_ATOMIC_REPRICE_REQUEST_V1' or
            row.get('direction') not in ('PUMP_TO_METEORA','METEORA_TO_PUMP') or
            type(row.get('size_lamports')) is not int or row['size_lamports'] not in GRID):
        return 'INVALID_CANONICAL_EVENT'
    if token not in inventory['ready']: return 'TOKEN_NOT_NATIVE_TWO_TEMPLATE_READY'
    pair = inventory['pairs'][token]
    if str(getattr(pair,'pump_pool','')) != row.get('pump_pool'):
        return 'PUMP_POOL_IDENTITY_MISMATCH'
    meteora = next((getattr(pair,k) for k in ('meteora_pool','dlmm_pool') if getattr(pair,k,None)),None)
    if meteora is None:
        return 'NATIVE_DLMM_IDENTITY_NOT_EXPOSED'
    if str(meteora) != row.get('meteora_pool'): return 'DLMM_POOL_IDENTITY_MISMATCH'
    return 'FULL_NATIVE_PAIR_IDENTITY_MATCH'

def observe(seconds, wallet):
    outcome = {'build':'FINAL_BOSS_NATIVE_STARTUP_REPLACEMENT','status':'HOLD',
        'phase':'freeze','broadcast':False,'signing':False,'signed_simulation':False,
        'rpc_per_candidate':0,'additional_websockets':0,'scanner_source_changed':False,
        'first_funded_canary_lamports':10_000_000,'source_rebinds':0,
        'new_events':0,'identity_matches':0,'native_transactions_prepared':0,
        'source_holds':{},'production_execution_certified':False}
    conn = None; sink = REPORT.with_name('oracle_402_transient_inbox.json')
    try:
        if not 1 <= seconds <= 90: raise Hold('OBSERVATION_WINDOW_INVALID')
        if not WALLET_RE.fullmatch(wallet): raise Hold('PUBLIC_WALLET_REQUIRED')
        outcome['source_hashes_verified']=freeze()
        scan=mod('oracle_344_scanner_align'); persistent=mod('oracle_374_persistent_dual_native_handoff')
        outcome['phase']='source_health_before_warm'
        first=persistent.read_heartbeat(scan)
        status=scanner_status(first)
        outcome.update(scanner_admitted=status['admitted'],scanner_status_source=status['source'],
                       scanner_epoch_before=first['epoch'],producer_prefix=first['producer'][:12])
        if not status['admitted']: raise Hold('SCANNER_HAS_NO_ADMITTED_PAIRS')
        outcome['phase']='native_startup_scoped_28'
        with native_capacity_scope() as scope:
            native=mod('oracle_370_native_atomic_executor')
            reverse=mod('oracle_378_native_reverse_atomic')
            provider=reverse.CompatibleNativeProvider(native,wallet)
            provider.prewarm()  # ONE canonical Q25 native hydration, no second discovery by default
        outcome.update(native_scope=scope,native_scope_restored=True)
        inv=native_inventory(provider)
        outcome.update({k:v for k,v in inv.items() if k not in ('registered','ready','pairs')})
        outcome['native_ready_vs_scanner']=str(inv['both_template_ready'])+'/'+str(status['admitted'])
        outcome['phase']='source_health_after_warm'
        after=persistent.read_heartbeat(scan)
        if after['producer']!=first['producer']: raise Hold('PRODUCER_CHANGED_DURING_NATIVE_WARM')
        outcome['scanner_epoch_after']=after['epoch']
        outcome['phase']='canonical_event_attachment'
        m363=mod('oracle_363_verified_scanner_bus_binding');m365=mod('oracle_365_sqlite_columnar_event_handoff')
        m379=mod('oracle_379_five_goal_executor');m359=mod('oracle_359_lock_safe_handoff')
        metrics=m379.Metrics(); Gate=m379.make_ingress(m363,metrics)
        counters=collections.Counter()
        def witness(row):
            outcome['new_events']+=1
            verdict=candidate_match(row,inv)
            counters[verdict]+=1
            if verdict=='FULL_NATIVE_PAIR_IDENTITY_MATCH':outcome['identity_matches']+=1
        def bind(db,h):
            gate=Gate(ttl_ms=2500,max_age_ms=1500)
            gate.callback=witness
            cursor=int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
            gate.attach(h,cursor)
            return gate
        with m359.ExclusiveLock():
            conn=scan.bus();conn.execute('PRAGMA query_only=ON');conn.execute('PRAGMA busy_timeout=500')
            hb=scan.validate_scanner(conn)
            if hb.get('ok') is not True or hb['producer']!=first['producer']:
                raise Hold('SOURCE_HEALTH_OR_PRODUCER_CHANGED_BEFORE_ATTACH')
            gate=bind(conn,hb);outcome['source_attached']=True
            deadline=time.monotonic()+seconds; next_health=0.0
            while time.monotonic()<deadline:
                if time.monotonic()>=next_health:
                    latest=scan.validate_scanner(conn)
                    if latest.get('ok') is not True or latest['producer']!=first['producer']:
                        raise Hold('SOURCE_PRODUCER_OR_HEALTH_INVALID')
                    if latest['epoch']!=hb['epoch']:
                        if not persistent.may_rebind(hb,latest):raise Hold('SOURCE_EPOCH_REBIND_NOT_SAFE')
                        gate=bind(conn,latest);outcome['source_rebinds']+=1
                        hb=latest;outcome['scanner_epoch_after']=hb['epoch']
                    else:
                        gate.health(latest)
                        if gate.failed:raise Hold('SOURCE_INGRESS_HEALTH_INVALID')
                    next_health=time.monotonic()+.25
                m365.consume(scan,conn,gate,collections.Counter(),sink)
                if gate.failed:raise Hold('SOURCE_COLUMNAR_INGRESS_FAILED')
                time.sleep(.005)
        outcome['source_holds']=dict(counters)
        current=scanner_status(hb);outcome['scanner_admitted_final']=current['admitted']
        if inv['both_template_ready']<current['admitted']:
            outcome['status']='HOLD_NATIVE_STARTUP_COVERAGE_SHORTFALL'
        elif outcome['identity_matches']<=0:
            outcome['status']='COUNT_COVERAGE_MET_IDENTITY_WITNESS_PENDING'
        else:
            outcome['status']='NATIVE_STARTUP_COUNT_AND_SAMPLED_IDENTITIES_MATCH_NOT_SIM_CERTIFIED'
        outcome['phase']='completed'
    except Exception as exc:
        outcome['status']='HOLD_'+safe(exc);outcome['source_holds']=dict(counters) if 'counters' in locals() else {}
    finally:
        if conn is not None:
            try:conn.close()
            except Exception:pass
        try:sink.unlink(missing_ok=True)
        except OSError:pass
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(outcome,indent=2,sort_keys=True),encoding='utf-8')
        print('[FINAL_BOSS_NATIVE_STARTUP]',json.dumps(outcome,sort_keys=True),flush=True)
        print('[REPORT]',REPORT.relative_to(ROOT),flush=True)
    return 0 if outcome['status'].startswith(('NATIVE_STARTUP_COUNT','COUNT_COVERAGE_MET')) else 2

def tests():
    class F: pass
    class P: pass
    class Old:
        READY_TOKENS={'a','b'}
        TEMPLATES={'a':{},'b':{}}
        METEORA_TEMPLATES={'a':{},'b':{}}
    f=F();f.pairs={'a':P(),'b':P()};f.programs={'a':'SPL','b':'SPL'}
    f.pairs['a'].pump_pool='P';f.pairs['a'].meteora_pool='D'
    prov=F();prov.forward=f;prov.old=Old()
    inv=native_inventory(prov)
    assert inv['both_template_ready']==2
    good={'schema':'ORACLE363_ATOMIC_REPRICE_REQUEST_V1','token':'a',
          'pump_pool':'P','meteora_pool':'D','size_lamports':15_000_000,'direction':'PUMP_TO_METEORA'}
    assert candidate_match(good,inv)=='FULL_NATIVE_PAIR_IDENTITY_MATCH'
    assert candidate_match(dict(good,meteora_pool='WRONG'),inv)=='DLMM_POOL_IDENTITY_MISMATCH'
    assert candidate_match(dict(good,size_lamports=1),inv)=='INVALID_CANONICAL_EVENT'
    Old.METEORA_TEMPLATES={'a':{}}
    assert native_inventory(prov)['both_template_ready']==1
    assert safe(RuntimeError('https://private?api-key=secret'))=='RUNTIMEERROR'
    assert len(GRID)==19
    import sys, types
    from unittest.mock import patch
    legacy='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot'
    stub=types.ModuleType(legacy)
    stub.engine=types.SimpleNamespace(MAX_TOKENS=4)
    stub.live_account_stream=types.SimpleNamespace(MAX_PAIRS=4)
    old_env=os.environ.get('QARB_HOT_PAIRS')
    with patch.dict(sys.modules,{legacy:stub}):
        try:
            with native_capacity_scope() as measured:
                assert measured['before_max_pairs']==4
                assert stub.live_account_stream.MAX_PAIRS==28 and stub.engine.MAX_TOKENS==28
                assert os.environ['QARB_HOT_PAIRS']=='28'
                raise ValueError('fixture abort')
        except ValueError: pass
    assert stub.live_account_stream.MAX_PAIRS==4 and stub.engine.MAX_TOKENS==4
    assert os.environ.get('QARB_HOT_PAIRS')==old_env
    print('[PASS] source-based native coverage, scoped startup restoration, full triple identity, 19 sizes, fail-closed, no signing')
    print('[SCOPE] Offline tests; scanner matching and native hydration require physical runtime')

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--observe',action='store_true')
    p.add_argument('--seconds',type=int,default=30)
    p.add_argument('--wallet',default=os.environ.get('QSB_SOLANA_WALLET',''))
    a=p.parse_args()
    if a.test: tests();return 0
    return observe(a.seconds,a.wallet)
if __name__=='__main__': raise SystemExit(main())
'''

def verify():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'oracle_402_source_first_handoff.py'
        p.write_text(SOURCE,encoding='utf-8');py_compile.compile(str(p),doraise=True)
    assert 'send'+'Transaction' not in SOURCE and 'sign_message(' not in SOURCE
    assert len(range(10_000_000,100_000_001,5_000_000))==19
    print('[PASS] FULL_REPLACEMENT 402: executor native startup scope=28, event rebinding, scanner frozen')

def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--install',action='store_true')
    a=ap.parse_args();verify()
    if a.test:return 0
    DEST.parent.mkdir(parents=True,exist_ok=True)
    if DEST.exists():
        current=DEST.read_bytes()
        # Windows Notepad / write_text normally use CRLF. Compare canonical text,
        # never raw platform-dependent bytes; retain a byte-exact preimage backup.
        try:
            normalized=DEST.read_text(encoding='utf-8-sig').replace('\r\n','\n').replace('\r','\n')
        except (UnicodeError,OSError):
            print('[HOLD] EXISTING_ORACLE402_UNREADABLE');return 2
        sha=hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        replacement_sha=hashlib.sha256(SOURCE.encode('utf-8')).hexdigest()
        if sha not in (OLD_SHA,replacement_sha):
            print('[HOLD] LOCAL_ORACLE402_UNKNOWN_SOURCE_NOT_OVERWRITTEN')
            print('[LOCAL_NORMALIZED_SHA256]',sha)
            return 2
        backup=ROOT/'runtime_state/oracle/final_boss_dual/oracle_402_source_before_consolidation.bak'
        backup.parent.mkdir(parents=True,exist_ok=True)
        if sha==OLD_SHA and not backup.exists():backup.write_bytes(current)
    tmp=DEST.with_name(DEST.name+'.full_replacement.tmp')
    tmp.write_text(SOURCE,encoding='utf-8');os.replace(tmp,DEST)
    print('[REPLACED_CANONICAL_EXECUTOR_STARTUP]',DEST.relative_to(ROOT))
    print('[PRESERVED] scanner 322/Q18/Q20/Q25, 370, 378, 379, original SDK packages')
    print('[SHA256]',hashlib.sha256(DEST.read_bytes()).hexdigest())
    return 0
if __name__=='__main__':raise SystemExit(main())
