from __future__ import annotations
import argparse, ast, builtins, hashlib, io, json, os
from pathlib import Path
from unittest.mock import patch

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_525_native_inventory_hydration.py'
SCANNER = BASE / 'boss_scanner_live.py'
REG = Path('runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json')
SHADOW = Path('runtime_state/oracle/oracle_live_execution/oracle_524/verified_candidate_registry.json')
R524 = SHADOW.with_name('handoff_report.json')
OUT = Path('runtime_state/oracle/oracle_live_execution/oracle_525/hydration_result.json')
B58 = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')

class Hold(RuntimeError):
    pass

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    if not Path(p).is_file():
        raise Hold('MISSING_' + Path(p).name)
    d = json.loads(Path(p).read_text(encoding='utf-8'))
    if not isinstance(d, dict):
        raise Hold('INVALID_JSON_' + Path(p).name)
    return d

def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_name(p.name + '.' + str(os.getpid()) + '.tmp')
    try:
        t.write_text(json.dumps(d, indent=2, sort_keys=True), encoding='utf-8')
        os.replace(t, p)
    finally:
        t.unlink(missing_ok=True)

def valid(x):
    return isinstance(x, str) and 32 <= len(x) <= 44 and set(x) <= B58

def native_candidate(canonical, shadow, qualified=None):
    if canonical.get('revision') != 'CHECKPOINT11_MULTI_POOL_REGISTRY_V1':
        raise Hold('CANONICAL_NATIVE_REVISION_CHANGED')
    if not isinstance(canonical.get('rows'), list) or not canonical['rows']:
        raise Hold('CANONICAL_ROWS_REQUIRED')
    if shadow.get('revision') != 'ORACLE524_HISTORICAL_QUOTE_CANDIDATES_V3':
        raise Hold('ORACLE524_V3_REQUIRED')
    rows = shadow.get('rows')
    if not isinstance(rows, list) or not rows:
        raise Hold('NO_VERIFIED_CANDIDATES')

    source = {}
    if qualified is not None:
        if not isinstance(qualified, list):
            raise Hold('QUALIFICATION_NOT_LIST')
        for row in qualified:
            if not isinstance(row, dict):
                continue
            key = str(row.get('token') or '') + '|' + str(row.get('meteora_pool') or '')
            if key in source and row != source[key]:
                raise Hold('QUALIFIED_DUPLICATE_CONFLICT')
            source[key] = row

    out = []
    seen = set()
    for r in rows:
        if not isinstance(r, dict):
            raise Hold('INVALID_SHADOW_ROW')
        t, p, m = (r.get(k) for k in ('token', 'pump_pool', 'meteora_pool'))
        if not all(valid(x) for x in (t, p, m)) or len({t, p, m}) != 3:
            raise Hold('INVALID_EXACT_POOL_IDENTITY')
        key = t + '|' + m
        if r.get('pair_key') != key or key in seen:
            raise Hold('PAIR_KEY_CONFLICT')
        if r.get('quote_observed_in_historical_521_window') is not True:
            raise Hold('UNQUOTED_SHADOW_ROW')
        seen.add(key)

        # Never copy vaults, arrays, or prices from unrelated tokens.
        native_row = {
            'pair_key': key, 'token': t,
            'pump_pool': p, 'meteora_pool': m
        }
        if qualified is not None:
            origin = source.get(key)
            if not origin or origin.get('pump_pool') != p:
                raise Hold('LIVE_QUALIFIED_POOL_IDENTITY_DRIFT')
            for f in ('token_x', 'token_y', 'decimals_x',
                      'decimals_y', 'array_count', 'reported_tvl'):
                v = origin.get(f)
                if f in ('token_x', 'token_y') and valid(v):
                    native_row[f] = v
                elif f in ('decimals_x', 'decimals_y') and isinstance(v, int) and 0 <= v <= 18:
                    native_row[f] = v
                elif f == 'array_count' and isinstance(v, int) and v >= 0:
                    native_row[f] = v
                elif f == 'reported_tvl' and isinstance(v, (float, int)) and v >= 0:
                    native_row[f] = v
        out.append(native_row)

    return {
        'revision': canonical['revision'],
        'identity': 'token|meteora_pool',
        'rows': out,
        'tokens': len({r['token'] for r in out}),
        'ready_pair_count': 0,
        'alternate_ready_count': 0,
        'gross_positive_count': 0,
        'failures': [],
        'temporary_runtime_cutover': True,
        'simulation': False,
        'execution_authority': False,
        'broadcast': False,
        'observed_unix': 0
    }

def isolated_hydrate(native, loader):
    # Substitute only reads of the canonical registry.
    # No production-registry disk writes.
    encoded = json.dumps(native, sort_keys=True).encode('utf-8')
    location = REG.resolve()
    path_open = Path.open
    basic_open = builtins.open
    replace = os.replace

    def match(path):
        try:
            return Path(path).resolve() == location
        except (TypeError, ValueError, OSError):
            return False

    def stream(mode):
        if any(c in mode for c in 'wax+'):
            raise Hold('PRODUCTION_REGISTRY_WRITE_BLOCKED')
        return io.BytesIO(encoded) if 'b' in mode else io.StringIO(encoded.decode())

    def guarded_path(self, mode='r', *a, **kw):
        return stream(mode) if match(self) else path_open(self, mode, *a, **kw)

    def guarded_open(file, mode='r', *a, **kw):
        return stream(mode) if match(file) else basic_open(file, mode, *a, **kw)

    def guarded_replace(src, dst, *a, **kw):
        if match(dst):
            raise Hold('PRODUCTION_REGISTRY_REPLACE_BLOCKED')
        return replace(src, dst, *a, **kw)

    with patch.object(Path, 'open', guarded_path), \
         patch('builtins.open', guarded_open), \
         patch('os.replace', guarded_replace):
        return loader()

def identity(pair):
    if isinstance(pair, dict):
        return (
            str(pair.get('token') or ''),
            str(pair.get('meteora_pool') or pair.get('dlmm_pool') or pair.get('lb_pair') or '')
        )
    return (
        str(getattr(pair, 'token', '')),
        str(getattr(pair, 'meteora_pool', None)
            or getattr(pair, 'dlmm_pool', None)
            or getattr(pair, 'lb_pair', None) or '')
    )

def run():
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('LIVE_EXECUTION_NOT_ARMED_BY_525')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('REMOVE_KEY_FROM_ISOLATED_CHILD_ONLY')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise Hold('RPC_URL_REQUIRED')

    report, canonical, shadow = read(R524), read(REG), read(SHADOW)
    if report.get('status') != 'PASS_524_HISTORICAL_QUOTE_PAIRS_JOINED':
        raise Hold('524_HANDOFF_PASS_REQUIRED')
    if sha(REG) != report.get('native_registry_hash') or \
       sha(SHADOW) != report.get('candidate_shadow_sha256'):
        raise Hold('524_SOURCE_HASH_DRIFT')

    frozen = (sha(SCANNER), sha(REG))

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_509_exact_pair_qualification as q509,
        oracle_510_warm_pair_preflight as q510
    )

    selection, total = q510.selected(q509.load(q510.CHECKS), 28)
    candidate = native_candidate(canonical, shadow, selection)
    expected = {r['token'] for r in candidate['rows']}

    print('[ORACLE525_START]', json.dumps({
        'verified_tokens': len(expected),
        'verified_pair_keys': len(candidate['rows']),
        'qualified_selected': len(selection),
        'production_registry_write': False,
        'signing': False, 'broadcast': False
    }), flush=True)

    try:
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            checkpoint17_pair_key_execution_templates as cp17
        )
        state, registry, failures = isolated_hydrate(
            candidate, cp17.c12._expanded_state
        )
        pairs = state.get('pairs', []) if isinstance(state, dict) else []
        if not isinstance(pairs, list):
            raise Hold('HYDRATED_PAIRS_NOT_LIST')

        loaded = {identity(x) for x in pairs}
        got = {t for t, p in loaded}
        target = {(r['token'], r['meteora_pool']) for r in candidate['rows']}
        if not got.issubset(expected):
            raise Hold('REGISTRY_INTERCEPT_NOT_PROVEN')

        exact = {(t, p) for t, p in loaded if (t, p) in target}
        complete = exact == target and not failures

        result = {
            'status': 'PASS_NATIVE_PAIR_HYDRATION_NO_EXECUTION'
                      if complete else 'HOLD_NATIVE_PAIR_HYDRATION_INCOMPLETE',
            'target_pair_keys': len(candidate['rows']),
            'hydrated_pairs': len(pairs),
            'verified_exact_pairs': len(exact),
            'unverified_exact_pair_keys': sorted(t + '|' + p for t, p in target - exact),
            'hydrated_distinct_tokens': len(got),
            'missing_tokens': sorted(expected - got),
            'failure_count': len(failures) if isinstance(failures, (list, dict)) else -1,
            'native_quote_freshness_certified': False,
            'signed_simulation_certified': False,
            'net_profitability_certified': False,
            'canary_size_sol': '0.010',
            'production_registry_unchanged': True,
            'scanner_unchanged': True,
            'signing': False, 'broadcast': False,
            'execution_authority': False
        }
    finally:
        if (sha(SCANNER), sha(REG)) != frozen:
            raise Hold('PROTECTED_DISK_BYTES_CHANGED')

    save(OUT, result)
    print('[ORACLE525_FINAL]', json.dumps(result, sort_keys=True), flush=True)
    return 0 if result['status'].startswith('PASS_') else 2

def tests():
    a, b, c = 'A'*32, 'B'*32, 'C'*32
    old = {
        'revision': 'CHECKPOINT11_MULTI_POOL_REGISTRY_V1',
        'rows': [{'token': c}]
    }
    new = {
        'revision': 'ORACLE524_HISTORICAL_QUOTE_CANDIDATES_V3',
        'rows': [{
            'token': a, 'pump_pool': b, 'meteora_pool': c,
            'pair_key': a + '|' + c,
            'quote_observed_in_historical_521_window': True
        }]
    }
    native = native_candidate(old, new)
    assert len(native['rows']) == 1
    assert native['rows'][0]['token'] == a
    assert not native['execution_authority']

    with patch.object(
        __import__('sys').modules[__name__],
        'REG', Path('__oracle_525_test_registry__.json')
    ):
        p = Path('__oracle_525_test_registry__.json')
        result = isolated_hydrate(native, lambda: json.loads(p.read_text()))
        assert result['rows'][0]['token'] == a

    try:
        native_candidate(old, {
            **new, 'rows': [{**new['rows'][0], 'pair_key': 'BAD'}]
        })
        raise AssertionError('BAD_KEY_ALLOWED')
    except Hold:
        pass

    print('[PASS] ORACLE525 native_rows_exact_pool_identity in_memory_intercept zero_broadcast', flush=True)

def install():
    if not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_MISSING')
    source = Path(__file__).read_text(encoding='utf-8')
    ast.parse(source)
    before = sha(SCANNER)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    temp = TARGET.with_name(TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(source, encoding='utf-8')
        os.replace(temp, TARGET)
    finally:
        temp.unlink(missing_ok=True)
    if sha(SCANNER) != before:
        raise Hold('SCANNER_CHANGED')
    print('[PASS] ORACLE525_FULL_INSTALL native_hydration_isolation', flush=True)

def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    for cmd in ('install', 'test', 'run'):
        group.add_argument('--' + cmd, action='store_true')
    args = ap.parse_args()
    try:
        if args.install:
            install()
            return 0
        if args.test:
            tests()
            return 0
        return run()
    except Exception as exc:
        if isinstance(exc, Hold):
            code = str(exc)
        elif isinstance(exc, KeyError) and exc.args and exc.args[0] in (
            'token_x', 'token_y', 'decimals_x', 'decimals_y',
            'array_count', 'reported_tvl', 'rows', 'pairs'
        ):
            code = 'NATIVE_HYDRATION_REQUIRED_FIELD_' + exc.args[0]
        else:
            code = type(exc).__name__
        print('[ORACLE525_HOLD]', code, flush=True)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())