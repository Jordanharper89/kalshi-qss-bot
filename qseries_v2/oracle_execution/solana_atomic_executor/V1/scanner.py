"""Oracle V1 scanner: exact bidirectional quote capture around frozen Q25/Q20/Q18.

V1 observes only. It never creates or sends transactions. Local Checkpoint-12/
ORACLE-525/526 must provide an executable exact-pair hydrated state.
"""
from __future__ import annotations
import argparse
import ast
import base64
import contextvars
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from unittest.mock import patch

ROOT = Path.cwd()
STATE = ROOT / 'runtime_state' / 'oracle' / 'V1'
BUS = STATE / 'opportunities.sqlite3'
REG = ROOT / 'runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json'
SHADOW = ROOT / 'runtime_state/oracle/oracle_live_execution/oracle_524/verified_candidate_registry.json'
R524 = SHADOW.with_name('handoff_report.json')
SCANNER = ROOT / 'qseries_v2/oracle_execution/solana_atomic_executor/boss_scanner_live.py'
SIZES = (0.010, 0.015, 0.025, 0.050, 0.100, 0.180, 0.280, 0.500, 1.000, 1.400)
CONTEXT = contextvars.ContextVar('oracle_v1_snapshot', default=None)
DIRECTIONS = ('PUMP_TO_METEORA', 'METEORA_TO_PUMP')

class Hold(RuntimeError):
    pass

class RemoteHTTP(Hold):
    def __init__(self, service, code, pool=None):
        self.service = service
        self.code = int(code)
        self.pool = pool
        super().__init__("%s_HTTP_%s%s" % (
            service, code, "_pool=" + pool[:12] if pool else ""))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj, dict):
        raise Hold('NON_OBJECT_JSON:' + path.name)
    return obj

def connect(path=BUS):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=5, isolation_level=None)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA busy_timeout=5000')
    db.execute('CREATE TABLE IF NOT EXISTS opportunities ('
               'id TEXT PRIMARY KEY, token TEXT NOT NULL, pool TEXT NOT NULL, '
               'direction TEXT NOT NULL, slot INTEGER NOT NULL, size_lamports INTEGER NOT NULL, '
               'created_ns INTEGER NOT NULL, expires_ns INTEGER NOT NULL, '
               'gross_local_lamports INTEGER NOT NULL, json TEXT NOT NULL)')
    db.execute('CREATE INDEX IF NOT EXISTS exp_idx ON opportunities(expires_ns)')
    return db

def candidate(token, pump, meteora, slot, generation, received_ns, quote,
              now_ns=None, ttl_ms=1500):
    now_ns = time.time_ns() if now_ns is None else now_ns
    if quote.get('direction') not in DIRECTIONS:
        raise Hold('UNKNOWN_DIRECTION')
    gross = int(quote['local_net'])
    if gross <= 0:
        return None
    size = int(round(float(quote['size_sol']) * 1_000_000_000))
    if size < 10_000_000 or size > 1_400_000_000:
        return None
    if not all(isinstance(s, str) and 32 <= len(s) <= 44 for s in (token, pump, meteora)):
        raise Hold('INVALID_EXACT_PAIR')
    if not isinstance(slot, int) or slot <= 0:
        raise Hold('INVALID_SLOT')
    if not 100 <= ttl_ms <= 2500:
        raise Hold('INVALID_TTL')
    # Receipt time is in a monotonic/perf-counter domain: do not compare it with wall time.
    if received_ns <= 0:
        raise Hold('MISSING_EVENT_MONOTONIC_RECEIPT')
    age_ms = (time.perf_counter_ns() - received_ns) / 1_000_000
    if age_ms < 0 or age_ms > ttl_ms:
        return None
    event = {'schema': 'ORACLE_V1_CANDIDATE_V1', 'token': token,
             'pump_pool': pump, 'meteora_pool': meteora,
             'pair_key': token + '|' + meteora, 'direction': quote['direction'],
             'size_lamports': size, 'local_gross_lamports': gross,
             'local_bps': float(quote.get('local_bps', 0)), 'slot': slot,
             'generation': int(generation), 'created_ns': now_ns,
             'expires_ns': now_ns + ttl_ms * 1_000_000,
             'read_only_quote': True, 'fee_adjusted': False,
             'simulation_passed': False, 'execution_authority': False}
    seed = '|'.join(map(str, (event['pair_key'], pump, event['direction'], slot,
                               generation, size, gross)))
    event['id'] = hashlib.sha256(seed.encode('utf-8')).hexdigest()
    return event

def publish(db, event):
    if event is None:
        return False
    raw = json.dumps(event, separators=(',', ':'), sort_keys=True)
    cur = db.execute('INSERT OR IGNORE INTO opportunities VALUES (?,?,?,?,?,?,?,?,?,?)',
                     (event['id'], event['token'], event['meteora_pool'],
                      event['direction'], event['slot'], event['size_lamports'],
                      event['created_ns'], event['expires_ns'],
                      event['local_gross_lamports'], raw))
    return cur.rowcount == 1

WSOL = 'So11111111111111111111111111111111111111112'
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MINT_OWNERS = {'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
               'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'}

def http_json(url, body=None):
    # No URL, HTTP error body, or Authorization token is ever printed.
    parsed = urllib.parse.urlsplit(url)
    pool_path = parsed.path.removeprefix('/pools/') if parsed.path.startswith('/pools/') else ''
    is_pool = (parsed.scheme == 'https' and
               parsed.hostname == 'dlmm.datapi.meteora.ag' and
               parsed.port is None and
               (parsed.path == '/pools' or
                (parsed.path.startswith('/pools/') and
                 '/' not in pool_path and 32 <= len(pool_path) <= 44)))
    is_rpc = (parsed.scheme == 'https' and
              parsed.hostname == 'mainnet.helius-rpc.com' and parsed.port is None)
    if body is None:
        if not is_pool:
            raise Hold('UNAPPROVED_POOL_METADATA_HOST')
        service = 'METEORA'
        req = urllib.request.Request(url, headers={
            'Accept': 'application/json',
            'User-Agent': 'OracleV1/1.1 (DLMM pool metadata; read-only)'})
    else:
        if not is_rpc:
            raise Hold('UNAPPROVED_RPC_HOST')
        service = 'HELIUS'
        req = urllib.request.Request(url, method='POST',
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json',
                     'Accept': 'application/json',
                     'User-Agent': 'OracleV1/1.1 (RPC; read-only)'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.load(response)
            if not isinstance(result, dict):
                raise Hold(service + '_INVALID_METADATA_RESPONSE')
            return result
        except urllib.error.HTTPError as exc:
            code = int(exc.code)
            # Bound temporary retries, never mask authentication failures.
            if code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(0.6 * (attempt + 1))
                continue
            raise RemoteHTTP(service, code, pool_path or None) from None
        except urllib.error.URLError as exc:
            if attempt < 2:
                time.sleep(0.6 * (attempt + 1))
                continue
            raise Hold(service + '_NETWORK_UNREACHABLE_' + type(exc.reason).__name__) from None
    raise Hold(service + '_REQUEST_RETRIES_EXHAUSTED')


def exact_pool_mints(response, pool, token):
    candidates = [response, response.get('data'), response.get('pool'), response.get('result')]
    info = None
    for item in candidates:
        for obj in (item if isinstance(item, list) else [item]):
            if isinstance(obj, dict) and (obj.get('address') or
                obj.get('pool_address') or obj.get('pubkey')) == pool:
                info = obj
                break
        if info is not None:
            break
    if info is None:
        raise Hold('POOL_IDENTITY_NOT_VERIFIED:' + token[:12])
    def mint(value):
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get('address') or value.get('mint') or value.get('token_address')
        return None
    x = mint(info.get('token_x') or info.get('tokenX'))
    y = mint(info.get('token_y') or info.get('tokenY'))
    if {x, y} != {token, WSOL} or x == y:
        raise Hold('POOL_TOKEN_ORIENTATION_MISMATCH:' + token[:12])
    return x, y


def pool_metadata(pool):
    base = 'https://dlmm.datapi.meteora.ag/pools'
    try:
        return http_json(base + '/' + pool)
    except RemoteHTTP as exc:
        if exc.service != 'METEORA' or exc.code not in (404, 410):
            raise
    print('[V1_METADATA_FALLBACK] exact_pool_404 query_by_address pool=' + pool[:12], flush=True)
    query = urllib.parse.urlencode({'query': pool, 'page_size': 20})
    data = http_json(base + '?' + query)
    entries = data.get('data')
    if not isinstance(entries, list) or not any(isinstance(x, dict) and
                 x.get('address') == pool for x in entries):
        raise Hold('METEORA_POOL_NOT_INDEXED:' + pool[:12])
    return data

def verified_decimals(info, token):
    if not isinstance(info, dict) or info.get('owner') not in MINT_OWNERS:
        raise Hold('MINT_OWNER_NOT_VERIFIED:' + token[:12])
    data = info.get('data')
    if not isinstance(data, list) or len(data) < 2 or data[1] != 'base64':
        raise Hold('MINT_ACCOUNT_ENCODING_INVALID')
    raw = base64.b64decode(data[0], validate=True)
    if len(raw) < 82 or raw[45] != 1 or raw[44] > 18:
        raise Hold('MINT_ACCOUNT_LAYOUT_INVALID')
    return int(raw[44])

def enrich(rows, pool_fetch, account_fetch):
    if not isinstance(rows, list) or not rows:
        raise Hold('NO_EXACT_POOL_ROWS')
    mints = {WSOL}
    pools = set()
    for row in rows:
        t, pool = row['token'], row['meteora_pool']
        x, y = exact_pool_mints(pool_fetch(pool), pool, t)
        for field, value in (('token_x', x), ('token_y', y)):
            if row.get(field) is not None and row[field] != value:
                raise Hold('MINT_ORIENTATION_DRIFT')
            row[field] = value
        mints.add(t)
        pools.add(pool)
    keys = sorted(mints | pools)
    result = account_fetch(keys)
    if result.get('error'):
        raise Hold('GET_MULTIPLE_ACCOUNTS_REJECTED')
    accounts = (result.get('result') or {}).get('value')
    if not isinstance(accounts, list) or len(accounts) != len(keys):
        raise Hold('ONCHAIN_ACCOUNT_READBACK_MISMATCH')
    by_address = dict(zip(keys, accounts))
    decimals = {mint: verified_decimals(by_address[mint], mint) for mint in mints}
    for pool in pools:
        if not isinstance(by_address.get(pool), dict) or by_address[pool].get('owner') != DLMM:
            raise Hold('DLMM_POOL_PROGRAM_OWNER_MISMATCH:' + pool[:12])
    for row in rows:
        row['decimals_x'] = decimals[row['token_x']]
        row['decimals_y'] = decimals[row['token_y']]
    return rows

def prepare_native():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_509_exact_pair_qualification as q509,
        oracle_510_warm_pair_preflight as q510,
        oracle_525_native_inventory_hydration as q525,
        checkpoint17_pair_key_execution_templates as cp17)
    report = read(R524)
    if report.get('status') != 'PASS_524_HISTORICAL_QUOTE_PAIRS_JOINED':
        raise Hold('ORACLE524_NOT_CERTIFIED')
    if digest(SHADOW) != report.get('candidate_shadow_sha256') or digest(REG) != report.get('native_registry_hash'):
        raise Hold('REGISTRY_LINEAGE_DRIFT')
    selected, _ = q510.selected(q509.load(q510.CHECKS), 28)
    native = q525.native_candidate(read(REG), read(SHADOW), selected)
    url = os.getenv('SOLANA_RPC_URL', '')
    if not url.startswith('https://mainnet.helius-rpc.com/'):
        raise Hold('HELIUS_SOLANA_RPC_URL_REQUIRED')
    def accounts(keys):
        return http_json(url, {'jsonrpc': '2.0', 'id': 1,
                               'method': 'getMultipleAccounts',
                               'params': [keys, {'encoding': 'base64', 'commitment': 'confirmed'}]})
    print('[V1_METADATA_START] pair_count=%d phase=METEORA_THEN_HELIUS' %
          len(native['rows']), flush=True)
    enrich(native['rows'], pool_metadata, accounts)
    print('[V1_METADATA_READY] exact_pair_mints_and_decimals_verified=%d' %
          len(native['rows']), flush=True)
    wanted = {(r['token'], r['meteora_pool']) for r in native['rows']}
    if not wanted or len(wanted) != len(native['rows']):
        raise Hold('DUPLICATE_OR_MISSING_EXACT_PAIRS')
    return native, wanted, cp17, q525

def hydrate():
    native, expected, cp17, q525 = prepare_native()
    frozen = (digest(SCANNER), digest(REG))
    try:
        state, registry, errors = q525.isolated_hydrate(native, cp17.c12._expanded_state)
    finally:
        if (digest(SCANNER), digest(REG)) != frozen:
            raise Hold('FROZEN_SOURCE_DRIFT')
    if errors or len(state.get('pairs') or []) != len(native['rows']):
        raise Hold('EXACT_PAIR_HYDRATION_INCOMPLETE')
    actual = {(str(p.token), str(p.meteora_pool)) for p in state['pairs']}
    if actual != expected:
        raise Hold('HYDRATED_PAIR_IDENTITY_MISMATCH')
    return state, expected

def run(seconds, ttl_ms):
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() == 'YES':
        raise Hold('SCANNER_CANNOT_ARM_EXECUTION')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('SCANNER_CHILD_MUST_NOT_RECEIVE_SIGNER')
    if not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_MISSING')
    state, expected = hydrate()
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    db = connect()
    original_price = r.canonical_price
    original_quote = r.q18.exact_snapshot_opportunities
    original_install = r.install_proven_hot_math
    received = [0, 0]
    token_pools = {str(p.token): (str(p.pump_pool), str(p.meteora_pool)) for p in state['pairs']}

    def intercept_price(lane, token, row):
        snap, slot, received_ns, generation = row
        marker = CONTEXT.set((token, slot, received_ns, generation))
        try:
            return original_price(lane, token, row)
        finally:
            CONTEXT.reset(marker)

    def quote_and_publish(snapshot, size):
        rows = original_quote(snapshot, size)
        meta = CONTEXT.get()
        if meta:
            token, slot, received_ns, generation = meta
            pump, meteora = token_pools[token]
            if (token, meteora) not in expected:
                raise Hold('CROSS_POOL_QUOTE_BLOCKED')
            for q in rows:
                if int(q.get('local_net', 0)) > 0:
                    event = candidate(token, pump, meteora, slot, generation, received_ns, q,
                                      ttl_ms=ttl_ms)
                    if publish(db, event):
                        received[0] += 1
                        print('[V1_SCANNER_NOMINATION]', event['direction'], token[:12],
                              'size_lamports=' + str(event['size_lamports']),
                              'LOCAL_ONLY_net=' + str(event['local_gross_lamports']), flush=True)
                received[1] += 1
        return rows

    def prepare_once(_root):
        return state, {'v1_exact_pairs': len(expected)}

    def install_and_hook(native_state):
        nonlocal original_quote
        warmed = original_install(native_state)
        # Hooks must be installed AFTER official hot math initialization.
        original_quote = r.q18.exact_snapshot_opportunities
        r.q18.exact_snapshot_opportunities = quote_and_publish
        return warmed

    print('[V1_SCANNER_START] pairs=%d TTL_ms=%d read_only=True' % (len(expected), ttl_ms), flush=True)
    try:
        with patch.object(r, 'canonical_price', intercept_price), \
             patch.object(r, 'install_proven_hot_math', install_and_hook), \
             patch.object(r, 'attack', lambda *a, **kw: None), \
             patch.object(r.q25, 'prepare_once', prepare_once):
            r.run(seconds)
    finally:
        r.q18.exact_snapshot_opportunities = original_quote
        db.close()
    print('[V1_SCANNER_FINAL] quote_rows=%d positive_nominations=%d broadcast=False' %
          (received[1], received[0]), flush=True)
    if received[1] == 0:
        raise Hold('CANONICAL_PRICING_HOOK_NOT_OBSERVED')

def repository_audit(repo=ROOT):
    totals = {'python_files': 0, 'parsed': 0, 'syntax_errors': 0,
              'zero_byte_modules': 0, 'signing_references': 0,
              'broadcast_references': 0, 'scanner_references': 0}
    failures = []
    for f in repo.rglob('*.py'):
        parts = set(f.relative_to(repo).parts)
        if parts & {'.git', 'venv', '.venv', '__pycache__', 'site-packages'}:
            continue
        totals['python_files'] += 1
        try:
            content = f.read_text(encoding='utf-8-sig')
            if not content:
                totals['zero_byte_modules'] += 1
                continue
            ast.parse(content, filename=str(f))
            totals['parsed'] += 1
            if 'sign_message' in content or 'sendTransaction' in content:
                totals['signing_references'] += int('sign_message' in content)
                totals['broadcast_references'] += int('sendTransaction' in content)
            if 'boss_scanner_live' in content:
                totals['scanner_references'] += 1
        except (SyntaxError, UnicodeError, OSError) as exc:
            totals['syntax_errors'] += 1
            if len(failures) < 100:
                failures.append({'path': str(f.relative_to(repo)), 'failure': type(exc).__name__})
    result = {'audit_kind': 'tree_wide_static_inventory_not_semantic_certification',
              'summary': totals, 'first_100_failures': failures,
              'native_checkpoint26_present': (repo / 'qseries_v2/oracle_execution/solana_atomic_executor' / 'checkpoint26_dlmm_output_ata_readiness.py').is_file()}
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / 'source_inventory.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
    print('[V1_SOURCE_INVENTORY]', json.dumps(totals, sort_keys=True), flush=True)
    print('[V1_SOURCE_AUDIT]', path, flush=True)


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        db = connect(Path(t) / 'candidate.sqlite3')
        good = candidate('A'*32, 'B'*32, 'C'*32, 101, 7, time.perf_counter_ns(),
                         {'direction': 'METEORA_TO_PUMP', 'size_sol': 0.010,
                          'local_net': 1000, 'local_bps': 10}, 1_000_000_000)
        assert publish(db, good) and not publish(db, good)
        assert db.execute('SELECT COUNT(*) FROM opportunities').fetchone()[0] == 1
        assert good['expires_ns'] == 2_500_000_000
        assert candidate('A'*32, 'B'*32, 'C'*32, 101, 7, time.perf_counter_ns(),
                         {'direction': 'PUMP_TO_METEORA', 'size_sol': .01, 'local_net': -1},
                         1_000_000_000) is None
        db.close()
    token, pool = 'A'*32, 'C'*32
    def mint(d):
        b = bytearray(82); b[44] = d; b[45] = 1
        return {'owner': next(iter(MINT_OWNERS)),
                'data': [base64.b64encode(b).decode('ascii'), 'base64']}
    def account_fetch(keys):
        values = {token: mint(6), WSOL: mint(9), pool: {'owner': DLMM}}
        return {'result': {'value': [values[k] for k in keys]}}
    sample = [{'token': token, 'meteora_pool': pool}]
    enrich(sample, lambda p: {'address': p, 'token_x': {'address': WSOL},
                              'token_y': {'address': token}}, account_fetch)
    assert sample[0]['decimals_x'] == 9 and sample[0]['decimals_y'] == 6
    try:
        exact_pool_mints({'address': pool, 'token_x': token,
                          'token_y': 'Z'*32}, pool, token)
        raise AssertionError('POOL_IDENTITY_BYPASS')
    except Hold: pass
    # HTTP error classification must not leak an RPC API key.
    fake = urllib.error.HTTPError('https://mainnet.helius-rpc.com/?api-key=SECRET',
                                  403, 'Forbidden', None, None)
    with patch.object(urllib.request, 'urlopen', side_effect=fake):
        try:
            http_json('https://mainnet.helius-rpc.com/?api-key=SECRET',
                      {'jsonrpc':'2.0','method':'getMultipleAccounts','params':[[]]})
            raise AssertionError('HTTP_AUTH_FAILURE_NOT_DETECTED')
        except RemoteHTTP as exc:
            assert exc.code == 403 and exc.service == 'HELIUS'
            assert 'SECRET' not in str(exc)
    # Meteora 404 tries documented indexed-pool lookup; only exact address is admitted.
    calls = []
    def mocked_metadata(url, body=None):
        calls.append(url)
        if len(calls) == 1:
            raise RemoteHTTP('METEORA', 404, pool)
        return {'data':[{'address': pool, 'token_x': token, 'token_y': WSOL}]}
    with patch.object(sys.modules[__name__], 'http_json', mocked_metadata):
        x, y = exact_pool_mints(pool_metadata(pool), pool, token)
        assert (x,y) == (token,WSOL) and len(calls)==2
    print('[PASS] V1_SCANNER durable_dedup both_directions onchain_decimals HTTP_status_redacted 404_exact_pool_fallback no_orders', flush=True)

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--run', action='store_true')
    g.add_argument('--test', action='store_true')
    g.add_argument('--audit-repo', action='store_true')
    ap.add_argument('--seconds', type=int, default=3600)
    ap.add_argument('--ttl-ms', type=int, default=1500)
    a = ap.parse_args()
    try:
        if a.test:
            self_test(); return 0
        if a.audit_repo:
            repository_audit(); return 0
        if not 10 <= a.seconds <= 43200 or not 100 <= a.ttl_ms <= 2500:
            raise Hold('INVALID_RUNTIME_BOUNDS')
        run(a.seconds, a.ttl_ms)
        return 0
    except Exception as exc:
        print('[V1_SCANNER_HOLD]', str(exc) if isinstance(exc, Hold) else type(exc).__name__, flush=True)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
