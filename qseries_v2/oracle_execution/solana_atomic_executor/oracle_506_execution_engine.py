from __future__ import annotations
"""One canonical Oracle executor observer, reusing frozen ORACLE-322 and native SDKs.

This module has no broadcast route. A signed simulation is opt-in, and never
constitutes authorization to transmit a transaction. No private key is persisted.
"""
import argparse
import collections
import contextlib
import importlib
import json
import os
import re
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = 'qseries_v2.oracle_execution.solana_atomic_executor'
BASE = ROOT / 'runtime_state/oracle/final_boss_dual'
REPORT = BASE / 'oracle_506_native_engine.json'
GRID = frozenset(range(10_000_000, 100_000_001, 5_000_000))
DIRECTIONS = ('PUMP_TO_METEORA', 'METEORA_TO_PUMP')
PUBKEY = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SAFE = re.compile(r'^[A-Z][A-Z0-9_]{3,90}$')

class Hold(RuntimeError):
    pass

def mod(name):
    return importlib.import_module(PKG + '.' + name)

def rate_limited(exc):
    # Recognize common upstream throttling without retaining RPC URLs or API keys.
    msg = str(exc).lower()
    return any(term in msg for term in ('429','too many requests','rate limit','throttl'))

def reason(err):
    s = str(err)
    return s if SAFE.fullmatch(s) else type(err).__name__.upper()

def snapshot_file(name, age_s=25):
    p = BASE / name
    try:
        if time.time() - p.stat().st_mtime > age_s:
            return None
        value = json.loads(p.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, UnicodeError):
        return None

def scanner_capacity(hb):
    for filename in ('scanner_status.json', 'scanner_live.json'):
        x = snapshot_file(filename)
        if x and x.get('epoch') == hb.get('epoch') and x.get('status', x.get('state')) == 'RUNNING':
            amount = x.get('admitted')
            if type(amount) is int and 0 <= amount <= 28:
                return amount
    raise Hold('SCANNER_FRESH_ADMITTED_COUNT_MISSING')

def scanner_identity_inventory(epoch, admitted):
    """Independent frozen scanner ORACLE147 report, not the executor's own discovery.

    Incomplete/stale reports are marked UNKNOWN rather than counted as certified.
    """
    path = ROOT / 'runtime_state/oracle/oracle_live_execution/ORACLE_147_WALLET_TEMPLATE_REPORT.json'
    try:
        if time.time() - path.stat().st_mtime > 30: return None, 'SCANNER147_REPORT_STALE'
        raw = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return None, 'SCANNER147_REPORT_UNAVAILABLE'
    if not isinstance(raw, dict): return None, 'SCANNER147_REPORT_FORMAT_UNKNOWN'
    if 'epoch' in raw and raw['epoch'] != epoch: return None, 'SCANNER147_EPOCH_DIFFERENT'
    found = set()
    queue = [raw]
    visited = 0
    while queue and visited < 5000:
        x = queue.pop(); visited += 1
        if isinstance(x, dict):
            t = x.get('token',x.get('mint'))
            p = x.get('pump_pool',x.get('pump'))
            m = x.get('meteora_pool',x.get('dlmm_pool',x.get('meteora')))
            if all(isinstance(z,str) and PUBKEY.fullmatch(z) for z in (t,p,m)):
                found.add((t,p,m))
            queue.extend(v for v in x.values() if isinstance(v,(dict,list)))
        elif isinstance(x,list):
            for v in x:
                if isinstance(v,(dict,list)):queue.append(v)
    if not found: return None, 'SCANNER147_NO_EXACT_TRIPLES_EXPOSED'
    if len(found) != admitted: return found, 'SCANNER147_TRIPLE_COUNT_DIFFERS_FROM_ADMITTED'
    return found, 'SCANNER147_TRIPLES_AVAILABLE'

def complete_identity_audit(epoch, admitted, inv):
    source, status = scanner_identity_inventory(epoch,admitted)
    native = set(inv['triples'].values())
    result = {'scanner_identity_source':status,'scanner_triples_available':len(source) if source is not None else 0,
              'native_triples_available':len(native),'all_scanner_identities_certified':False}
    if source is not None:
        result['missing_native_triples'] = len(source-native)
        result['extra_native_triples'] = len(native-source)
        result['all_scanner_identities_certified'] = (status=='SCANNER147_TRIPLES_AVAILABLE' and
                   source==native and len(native)==admitted)
    return result

@contextlib.contextmanager
def native_capacity_scope():
    """Scoped executor hydration only. Does not mutate disk or scanner process."""
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine, live_account_stream as stream
    old = (stream.MAX_PAIRS, engine.MAX_TOKENS)
    keys = ('QARB_HOT_PAIRS', 'QARB_MAX_TOKENS')
    env = {k: os.environ.get(k) for k in keys}
    try:
        stream.MAX_PAIRS = engine.MAX_TOKENS = 28
        os.environ['QARB_HOT_PAIRS'] = '28'
        os.environ['QARB_MAX_TOKENS'] = '28'
        yield
    finally:
        stream.MAX_PAIRS, engine.MAX_TOKENS = old
        for k in keys:
            if env[k] is None: os.environ.pop(k, None)
            else: os.environ[k] = env[k]

def _pair_value(pair, *names):
    for name in names:
        value = pair.get(name) if isinstance(pair,dict) else getattr(pair,name,None)
        if isinstance(value,dict):
            value = value.get('address',value.get('pubkey',value.get('pool')))
        if value is not None and str(value):return str(value)
    return None

def native_inventory(provider):
    forward = getattr(provider, 'forward', None)
    old = getattr(provider, 'old', None)
    pairs = getattr(forward, 'pairs', None)
    if not isinstance(pairs, dict):
        raise Hold('NATIVE_REGISTRY_UNAVAILABLE')
    sets = [set(map(str, getattr(old, 'READY_TOKENS', ()))),
            set(map(str, getattr(old, 'TEMPLATES', {}))),
            set(map(str, getattr(old, 'METEORA_TEMPLATES', {}))),
            set(map(str, getattr(forward, 'programs', {})))]
    ready = set(map(str, pairs)).intersection(*sets)
    triples = {}
    unidentified = []
    for token in sorted(ready):
        pair = pairs.get(token)
        pump = _pair_value(pair, 'pump_pool','pump')
        dlmm = _pair_value(pair, 'meteora_pool','dlmm_pool','meteora','dlmm')
        if not pump or not dlmm:
            unidentified.append(token[:12])
            continue
        triples[token] = (str(token), str(pump), str(dlmm))
    return {'pairs': pairs, 'ready': ready, 'triples': triples,
            'counts': {'native_pairs': len(pairs), 'two_template_ready': len(ready),
                       'full_native_triples_exposed': len(triples),
                       'triple_field_unavailable': len(unidentified),
                       'missing_native_tokens': len(set(map(str, pairs)) - ready)},
            'unidentified': unidentified[:12]}

def witness(row, inv):
    if row.get('schema') != 'ORACLE363_ATOMIC_REPRICE_REQUEST_V1':
        return 'HOLD_BAD_SCHEMA'
    if row.get('direction') not in DIRECTIONS or type(row.get('size_lamports')) is not int or row['size_lamports'] not in GRID:
        return 'HOLD_INVALID_DIRECTION_OR_SIZE'
    token = row.get('token')
    if token not in inv['ready']:
        return 'HOLD_TOKEN_NOT_WARM'
    triple = inv['triples'].get(token)
    if triple is None:
        return 'HOLD_NATIVE_TRIPLE_UNEXPOSED'
    if triple != (token, row.get('pump_pool'), row.get('meteora_pool')):
        return 'HOLD_POOL_TRIPLE_DIFFERENT'
    return 'EXACT_TRIPLE_MATCH'

def evaluate_fixture(rows):
    """Deterministic historical/fixture handoff; never speaks to RPC or wallet."""
    best = None
    for r in rows:
        if r.get('direction') not in DIRECTIONS or r.get('size_lamports') not in GRID:
            continue
        gross = r.get('scanner_gross_lamports_hint')
        if type(gross) is not int or gross <= 0: continue
        if best is None or gross > best['scanner_gross_lamports_hint']:
            best = r
    return best

class LatestCandidates:
    """Small coalescing queue, scans stay on the SQLite reader's fast thread."""
    def __init__(self):
        self.cv = threading.Condition()
        self.pending = {}
        self.inflight = set()
        self.closed = False
        self.dropped = collections.Counter()
    def put(self, row):
        key = (row['token'], row['direction'])
        with self.cv:
            if self.closed: return
            old = self.pending.get(key)
            if old is not None and old['event_id'] >= row['event_id']:
                self.dropped['older'] += 1; return
            self.pending[key] = row
            self.cv.notify()
    def get(self, stop, seconds=.10):
        with self.cv:
            if not self.pending and not stop.is_set(): self.cv.wait(seconds)
            if stop.is_set() or self.closed or not self.pending: return None
            # Highest positive hint is nomination priority only, not true net.
            key = max(self.pending, key=lambda k: self.pending[k]['scanner_gross_lamports_hint'])
            return self.pending.pop(key)
    def close(self):
        with self.cv:
            self.closed = True
            self.pending.clear()
            self.cv.notify_all()

def sealed_nonce(row):
    return (str(row['scanner_producer']), int(row['scanner_epoch']), int(row['event_id']))

def precheck(row, producer, epoch, now_ms=None):
    if row.get('scanner_producer') != producer or row.get('scanner_epoch') != epoch:
        return 'PRODUCER_OR_EPOCH_DRIFT'
    if type(row.get('size_lamports')) is not int or row['size_lamports'] not in GRID:
        return 'SIZE_OUTSIDE_SUPPORTED_CURVE'
    if row.get('direction') not in DIRECTIONS:
        return 'INVALID_DIRECTION'
    exp = row.get('expires_at_unix_ms')
    now = int(time.time()*1000) if now_ms is None else now_ms
    if type(exp) is not int or now >= exp:
        return 'CANDIDATE_STALE_BEFORE_NATIVE_PREPARE'
    if row.get('scanner_gross_lamports_hint',0) <= 0:
        return 'NONPOSITIVE_SCANNER_NOMINATION'
    return None

def proof_contract(row, proof, bank_gate):
    if not isinstance(proof, dict): raise Hold('NATIVE_PROOF_MISSING')
    for field in ('event_id', 'token', 'direction', 'size_lamports', 'pump_pool', 'meteora_pool'):
        if proof.get(field) != row[field]: raise Hold('NATIVE_PROOF_IDENTITY_MISMATCH')
    if not all(proof.get(k) is True for k in ('single_bank_context_verified', 'native_unsigned', 'alt_resolved', 'atomic_single_transaction')):
        raise Hold('NATIVE_SAME_BANK_V0_ALT_NOT_PROVEN')
    if proof.get('version') != 0 or type(proof.get('serialized_bytes')) is not int or not 0 < proof['serialized_bytes'] <= 1232:
        raise Hold('NATIVE_V0_PACKET_INVALID')
    if proof.get('legs') != (['PUMP_BUY', 'DLMM_SELL'] if row['direction'] == 'PUMP_TO_METEORA' else ['DLMM_BUY', 'PUMP_SELL']):
        raise Hold('NATIVE_LEG_ORDER_MISMATCH')
    x = bank_gate(row, proof)
    if x: raise Hold('NATIVE_BANK_GATE_REJECTED')
    return True

def load_historical_fixture(path):
    """Fixture is evaluated structurally only; cannot be used for an execution pass."""
    if not path: return None
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 1_000_000: raise Hold('FIXTURE_NOT_AVAILABLE_OR_TOO_LARGE')
    x = json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(x, list): raise Hold('FIXTURE_MUST_BE_JSON_ARRAY')
    return x

def work(seconds, wallet, signed_sim=False, fixture=None):
    if not 1 <= seconds <= 3600: raise Hold('RUN_BOUNDS_INVALID')
    if not PUBKEY.fullmatch(wallet): raise Hold('PUBLIC_WALLET_REQUIRED')
    state = {'build':'ORACLE506_EXACT_NATIVE_TARGETED_EXECUTOR','status':'HOLD',
             'scanner_modified':False,'additional_websockets':0,'broadcast':False,
             'signed_sim_requested':bool(signed_sim),'signed_sim_successes':0,
             'protected_net_profit_certified':False,'production_execution_certified':False,
             'recommended_size_lamports':None,'best_signed_sim_candidate_size_lamports':None,'events_received':0,
             'real_nominees':0,'native_attempts':0,'native_unsigned':0,
             'exact_identity_matches':0,'rebinds':0,'replenishment_attempts':0,
             'source_holds':{},'native_holds':{},'phase':'preflight'}
    stop = threading.Event()
    queue = LatestCandidates()
    ledger = set()
    counters = collections.Counter()
    db = None
    worker = None
    inbox = BASE / 'oracle_506_transient_inbox.json'
    state_lock = threading.Lock()
    provider_lock = threading.Lock()
    provider = None
    inv = None
    first = None
    hb = None
    try:
        owner = mod('oracle_399_final_boss_execution_owner')
        if len(owner.source_hashes()) != 4: raise Hold('SCANNER_FROZEN_HASH_SET_INVALID')
        scan = mod('oracle_344_scanner_align')
        persistent = mod('oracle_374_persistent_dual_native_handoff')
        first = persistent.read_heartbeat(scan)
        hb = first
        initial_count = scanner_capacity(hb)
        state['scanner_admitted_initial'] = initial_count
        state['scanner_epoch_start'] = hb['epoch']
        state['phase'] = 'native_hydration_deferred_to_positive_event'
        native = mod('oracle_370_native_atomic_executor')
        reverse = mod('oracle_378_native_reverse_atomic')
        exact_hydration = mod('oracle_506_targeted_native_hydration')
        # Reuse scanner selection. NO second blanket crosslist discovery or 28-pair
        # prewarm: it duplicated the scanner's RPC calls and caused HTTP 429.
        # Only a FRESH, POSITIVE canonical event can request token-specific native warm.
        with native_capacity_scope():
            provider = reverse.CompatibleNativeProvider(native, wallet)
        if not callable(getattr(provider, 'controlled_replenish', None)):
            raise Hold('ON_DEMAND_NATIVE_PROVIDER_METHOD_MISSING')
        try:
            inv = native_inventory(provider)
        except Hold as exc:
            if str(exc) != 'NATIVE_REGISTRY_UNAVAILABLE': raise
            inv = {'pairs':{}, 'ready':set(), 'triples':{},
                   'counts':{'native_pairs':0,'two_template_ready':0,
                             'full_native_triples_exposed':0,'triple_field_unavailable':0,
                             'missing_native_tokens':0}, 'unidentified':[]}
        state['native_hydration_policy']='SCANNER_EXACT_TRIPLE_ON_DEMAND_ONLY'
        state['blanket_prewarm_calls']=0
        state['on_demand_warm_attempts']=0
        state['on_demand_warm_completed']=0
        state['on_demand_rpc_cooldowns']=0
        state.update(inv['counts'])
        state['count_coverage_initial'] = str(len(inv['ready'])) + '/' + str(initial_count)
        state.update(complete_identity_audit(hb['epoch'],initial_count,inv))
        if len(inv['ready']) < initial_count:
            # Leave subscriber active for evidence, but never claim full coverage.
            state['startup_shortfall'] = initial_count - len(inv['ready'])
        state['phase'] = 'canonical_reader_attached_without_blanket_prewarm'
        m363 = mod('oracle_363_verified_scanner_bus_binding')
        m365 = mod('oracle_365_sqlite_columnar_event_handoff')
        m379 = mod('oracle_379_five_goal_executor')
        m359 = mod('oracle_359_lock_safe_handoff')
        core = mod('oracle_368_source_boundary_repair')
        bridge = mod('oracle_401_canonical_signed_preflight') if signed_sim else None
        if signed_sim:
            from qseries_v2.oracle_execution.solana_atomic_executor import oracle_503_sim_credential_store as secvault
            signer_pub, signing_secret = secvault.load_signer()
            if signer_pub != wallet:raise Hold('VAULT_SIGNER_WALLET_MISMATCH')
            key = secvault._keypair(signing_secret)
            del signing_secret
        else:key = None
        # Signer key remains only in worker memory; no key bytes in reports.
        metrics = m379.Metrics()
        Ingress = m379.make_ingress(m363, metrics)
        ingest = Ingress(ttl_ms=2500,max_age_ms=1500)
        source = {'producer':hb['producer'], 'epoch':hb['epoch']}
        gate_counts = collections.Counter()
        
        def receive(row):
            with state_lock:
                state['events_received'] += 1
            row = dict(row)
            row.pop('first_funded_canary_lamports',None)
            result = precheck(row,source['producer'],source['epoch'])
            if result:
                with state_lock:counters[result] += 1
                return
            with state_lock:
                state['real_nominees'] += 1
                state['last_candidate_ingress_age_ms'] = row.get('source_age_at_ingress_ms')
            queue.put(row)
        ingest.callback = receive
        
        retry_not_before = {}
        def worker_loop():
            nonlocal inv
            while not stop.is_set():
                row = queue.get(stop)
                if row is None: continue
                issue = precheck(row,source['producer'],source['epoch'])
                if issue:
                    with state_lock:counters[issue] += 1
                    continue
                nonce = sealed_nonce(row)
                with state_lock:
                    if nonce in ledger:
                        counters['DUPLICATE_EVENT'] += 1
                        continue
                    ledger.add(nonce)
                    state['native_attempts'] += 1
                try:
                    start_prepare = time.perf_counter()
                    with provider_lock:
                        current = native_inventory(provider)
                        verdict = witness(row,current)
                        if verdict != 'EXACT_TRIPLE_MATCH':
                            if verdict == 'HOLD_TOKEN_NOT_WARM':
                                tok = row['token']
                                if time.monotonic() < retry_not_before.get(tok, 0):
                                    raise Hold('TOKEN_RPC_COOLDOWN')
                                # Do not reprice or reuse the old candidate after RPC warm.
                                # Revalidate the same exact triple and candidate expiry.
                                with state_lock:state['on_demand_warm_attempts']+=1
                                try:
                                    with native_capacity_scope():warm_result = exact_hydration.exact_native_refresh(provider,row,expected_wallet=wallet)
                                    inv = native_inventory(provider)
                                    if witness(row,inv) != 'EXACT_TRIPLE_MATCH':
                                        raise Hold('TARGET_NATIVE_TEMPLATES_NOT_EXACTLY_READY')
                                    with state_lock:
                                        state['on_demand_warm_completed'] += 1
                                        state['two_template_ready'] = len(inv['ready'])
                                        state['exact_native_last_token_prefix'] = tok[:12]
                                    # Absolutely do not trade the nomination that paid
                                    # for hydration; require the next canonical event.
                                    raise Hold('TARGET_WARMED_WAIT_NEW_EVENT')
                                except Exception as warm_error:
                                    label=reason(warm_error)
                                    if label.startswith('TARGET_RPC_429_') or rate_limited(warm_error):
                                        retry_not_before[tok] = time.monotonic()+45.0
                                        with state_lock:state['on_demand_rpc_cooldowns']+=1
                                        raise Hold('TARGET_RPC_RATE_LIMIT_COOLDOWN') from None
                                    if label != 'TARGET_WARMED_WAIT_NEW_EVENT':
                                        retry_not_before[tok] = time.monotonic()+8.0
                                        with state_lock:
                                            state['last_hydration_hold']=label
                                    raise
                                current = native_inventory(provider)
                                inv = current
                                verdict = witness(row,current)
                                if precheck(row,source['producer'],source['epoch']):
                                    raise Hold('STALE_DURING_NATIVE_WARM')
                            if verdict != 'EXACT_TRIPLE_MATCH': raise Hold(verdict)
                        with state_lock:state['exact_identity_matches'] += 1
                        if precheck(row,source['producer'],source['epoch']):
                            raise Hold('STALE_AFTER_IDENTITY')
                        proof = provider.prepare_unsigned(row)
                        proof_contract(row,proof,core.bank_native_gate)
                        with state_lock:
                            state['native_unsigned'] += 1
                            state['last_native_prepare_ms'] = round((time.perf_counter()-start_prepare)*1000,3)
                            state['last_native_direction'] = row['direction']
                            state['last_native_size_lamports'] = row['size_lamports']
                        if signed_sim:
                            if stop.is_set() or precheck(row,source['producer'],source['epoch']):
                                raise Hold('STALE_BEFORE_SIGNED_SIM')
                            # Known reverse SDK program mismatch remains a hard hold.
                            if row['direction']=='METEORA_TO_PUMP' and bridge.checks()['reverse_validator_program_id_drift']:
                                raise Hold('REVERSE_PROGRAM_ID_DRIFT')
                            signed = bridge.signed_preflight(row,proof,wallet,key,native._rpc)
                            if not isinstance(signed,dict) or 'fee_adjusted_conservative_sim_net_lamports' not in signed:
                                raise Hold('SIGNED_SIM_ECONOMICS_INCOMPLETE')
                            net = signed['fee_adjusted_conservative_sim_net_lamports']
                            if type(net) is not int or net <= 0:raise Hold('SIGNED_SIM_NET_NOT_POSITIVE')
                            # Existing signed preflight says minimum-out protection NOT YET CERTIFIED.
                            with state_lock:
                                state['signed_sim_successes'] += 1
                                state['best_sim_seen_net_lamports'] = max(net,state.get('best_sim_seen_net_lamports',0))
                                if state['best_sim_seen_net_lamports']==net:
                                    state['best_signed_sim_candidate_size_lamports'] = row['size_lamports']
                                    state['recommended_direction'] = row['direction']
                                state['signed_sim_protected_min_out'] = False
                except Exception as exc:
                    with state_lock:counters[reason(exc)] += 1
                finally:
                    # No raw transaction bytes or secrets retained.
                    row.clear()
        
        worker = threading.Thread(target=worker_loop,name='oracle402_native_nonbroadcast',daemon=True)
        worker.start()
        with m359.ExclusiveLock():
            db = scan.bus()
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA busy_timeout=500')
            hb = scan.validate_scanner(db)
            if hb.get('ok') is not True or hb['producer']!=first['producer']:
                raise Hold('SCANNER_CHANGED_BEFORE_EVENT_ATTACH')
            def attach(new_hb):
                ingest.latest.clear()
                ingest.deadlines.clear()
                ingest.failed = False
                cursor = int(db.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
                ingest.attach(new_hb,cursor)
                source.update(producer=new_hb['producer'],epoch=new_hb['epoch'])
                return cursor
            attach(hb)
            state['source_attached']=True
            state['phase']='live_readonly_on_demand_native'
            started=time.monotonic()
            next_health=0
            next_inventory=0
            next_report=0
            last_count=initial_count
            while time.monotonic()-started < seconds:
                now=time.monotonic()
                if now>=next_health:
                    latest = scan.validate_scanner(db)
                    if latest.get('ok') is not True:raise Hold('SCANNER_HEALTH_FAILED')
                    if latest['producer'] != hb['producer']:
                        raise Hold('SCANNER_PRODUCER_CHANGED_NEEDS_NEW_SESSION')
                    if latest['epoch'] != hb['epoch']:
                        if not persistent.may_rebind(hb,latest):
                            raise Hold('SCANNER_EPOCH_NOT_SAFE_TO_REBIND')
                        attach(latest)
                        hb=latest
                        with state_lock:state['rebinds']+=1
                        # Prior event proposals are never reused after an epoch change.
                        with queue.cv:queue.pending.clear()
                    else:
                        ingest.health(latest)
                        if ingest.failed:raise Hold('INGRESS_SOURCE_HEALTH_FAILED')
                    next_health=now+.25
                if now>=next_inventory:
                    admitted=scanner_capacity(hb)
                    with state_lock:state['scanner_admitted_current']=admitted
                    # Account changes are observed without issuing ANY RPC.
                    # Candidate-driven native hydration occurs in worker_loop.
                    if admitted != last_count:
                        last_count = admitted
                        with state_lock:state['scanner_inventory_changes']=state.get('scanner_inventory_changes',0)+1
                    with provider_lock:
                        audit = complete_identity_audit(hb['epoch'],admitted,inv)
                    with state_lock:state.update(audit)
                    next_inventory=now+2
                m365.consume(scan,db,ingest,gate_counts,inbox)
                if ingest.failed:raise Hold('COLUMNAR_INGRESS_FAILED')
                if now>=next_report:
                    with state_lock:
                        state['native_holds']=dict(counters)
                        state['new_events_accepted']=state['events_received']
                        pulse={k:state.get(k) for k in ('scanner_admitted_current','two_template_ready','all_scanner_identities_certified','events_received','native_attempts','native_unsigned','signed_sim_successes','rebinds')}
                    print('[FINAL_BOSS_PULSE]',json.dumps(pulse,sort_keys=True),flush=True)
                    next_report=now+15
                time.sleep(.005)
        state['status']='OBSERVED_NO_TRADE_SENT'
        state['phase']='finished'
    except Exception as exc:
        state['status']='HOLD_'+reason(exc)
    finally:
        stop.set();queue.close()
        if worker is not None: worker.join(timeout=2.0)
        if db is not None:
            try:db.close()
            except Exception:pass
        try:inbox.unlink(missing_ok=True)
        except OSError:pass
        with state_lock:
            state['native_holds']=dict(counters)
            state['source_holds']=dict(gate_counts) if 'gate_counts' in locals() else {}
            state['queue_dropped']=dict(queue.dropped)
            state['scanner_epoch_final']=source['epoch'] if 'source' in locals() else None
        state['source_freeze_sha_count']=4 if state.get('scanner_admitted_initial') is not None else 0
        state['wallet_public_only']=wallet[:8]+'...'
        BASE.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(state,sort_keys=True,indent=2),encoding='utf-8')
        print('[ORACLE501_NATIVE_ENGINE]',json.dumps(state,sort_keys=True),flush=True)
        print('[REPORT]',REPORT.relative_to(ROOT),flush=True)
    return 0 if state['status']=='OBSERVED_NO_TRADE_SENT' else 2

def tests():
    rows = [dict(direction='METEORA_TO_PUMP',size_lamports=20_000_000,scanner_gross_lamports_hint=100),
            dict(direction='PUMP_TO_METEORA',size_lamports=30_000_000,scanner_gross_lamports_hint=300),
            dict(direction='PUMP_TO_METEORA',size_lamports=25_000_000,scanner_gross_lamports_hint=-900)]
    assert evaluate_fixture(rows)['size_lamports']==30_000_000
    assert len(GRID)==19 and len(DIRECTIONS)==2
    assert complete_identity_audit(1,1,{'triples':{}})['all_scanner_identities_certified'] is False
    class F:pass
    class Old:
        READY_TOKENS={'t'};TEMPLATES={'t':1};METEORA_TEMPLATES={'t':1}
    forward=F();forward.pairs={'t':F()};forward.programs={'t':'SPL'}
    forward.pairs['t'].pump_pool='p';forward.pairs['t'].meteora_pool='d'
    provider=F();provider.forward=forward;provider.old=Old()
    inv=native_inventory(provider)
    assert inv['counts']['two_template_ready']==1
    assert _pair_value({'meteora':{'address':'DUMMY'}},'meteora')=='DUMMY'
    row = dict(schema='ORACLE363_ATOMIC_REPRICE_REQUEST_V1',token='t',pump_pool='p',meteora_pool='d',direction='PUMP_TO_METEORA',size_lamports=20_000_000)
    assert witness(row,inv)=='EXACT_TRIPLE_MATCH'
    assert witness(dict(row,meteora_pool='OTHER'),inv)=='HOLD_POOL_TRIPLE_DIFFERENT'
    assert precheck(dict(row,scanner_epoch=5,scanner_producer='X',scanner_gross_lamports_hint=1,expires_at_unix_ms=2000),'X',5,now_ms=1000) is None
    assert precheck(dict(row,scanner_epoch=5,scanner_producer='X',scanner_gross_lamports_hint=1,expires_at_unix_ms=2000),'X',5,now_ms=3000)=='CANDIDATE_STALE_BEFORE_NATIVE_PREPARE'
    assert reason(RuntimeError('https://example?api-key=secret'))=='RUNTIMEERROR'
    q=LatestCandidates();a={'token':'t','direction':'PUMP_TO_METEORA','event_id':1,'scanner_gross_lamports_hint':1}
    q.put(a);q.put(dict(a,event_id=2));assert q.get(threading.Event())['event_id']==2
    q.close()
    proof = {'event_id':7,'token':'t','direction':'PUMP_TO_METEORA','size_lamports':20_000_000,'pump_pool':'p','meteora_pool':'d','single_bank_context_verified':True,'native_unsigned':True,'alt_resolved':True,'atomic_single_transaction':True,'version':0,'serialized_bytes':900,'legs':['PUMP_BUY','DLMM_SELL']}
    assert proof_contract(dict(row,event_id=7),proof,lambda *_:None)
    try:proof_contract(dict(row,event_id=7),dict(proof,version=1),lambda *_:None)
    except Hold:pass
    else:raise AssertionError('BAD_VERSION_ACCEPTED')
    import sys,types
    from unittest.mock import patch
    legacy='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot'
    stub=types.ModuleType(legacy);stub.engine=types.SimpleNamespace(MAX_TOKENS=12);stub.live_account_stream=types.SimpleNamespace(MAX_PAIRS=4)
    old = os.environ.get('QARB_HOT_PAIRS')
    with patch.dict(sys.modules,{legacy:stub}):
        with native_capacity_scope():
            assert stub.engine.MAX_TOKENS == 28 and stub.live_account_stream.MAX_PAIRS == 28
    assert stub.engine.MAX_TOKENS==12 and stub.live_account_stream.MAX_PAIRS==4
    assert os.environ.get('QARB_HOT_PAIRS')==old
    assert rate_limited(RuntimeError('HTTP Error 429: Too Many Requests'))
    assert not rate_limited(RuntimeError('POOL_MISMATCH'))
    # OFFLINE source-level invariant: never invoke a blanket native prewarm.
    import inspect
    active=inspect.getsource(work)
    assert 'provider.prewarm()' not in active
    assert 'exact_hydration.exact_native_refresh(provider,row,expected_wallet=wallet)' in active
    assert 'TARGET_RPC_RATE_LIMIT_COOLDOWN' in active
    assert 'STALE_DURING_NATIVE_WARM' in active
    print('[PASS] ORACLE_504_TARGETED_NATIVE full native startup, source epoch, both directions, 19 sizes, in-memory queue, signed preflight gate, scanner untouched')
    print('[SCOPE] deterministic offline fixtures; live native signed simulation is not yet certified')

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true')
    g.add_argument('--observe',action='store_true')
    g.add_argument('--fixture',type=str,default='')
    p.add_argument('--signed-sim',action='store_true')
    p.add_argument('--seconds',type=int,default=90)
    p.add_argument('--wallet',default=os.environ.get('QSB_SOLANA_WALLET',''))
    a=p.parse_args()
    if a.test:tests();return 0
    if a.fixture:
        rows=load_historical_fixture(a.fixture)
        best=evaluate_fixture(rows)
        print('[OFFLINE_FIXTURE_ONLY]',json.dumps({'best_gross_nomination_lamports':best.get('scanner_gross_lamports_hint') if best else None,'best_size_lamports':best.get('size_lamports') if best else None,'eligible_count':len(rows),'broadcast':False,'actual_profit_certified':False},sort_keys=True))
        return 0
    return work(a.seconds,a.wallet,signed_sim=a.signed_sim)

if __name__ == '__main__':
    raise SystemExit(main())
