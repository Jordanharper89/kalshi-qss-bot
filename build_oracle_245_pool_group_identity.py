"""ORACLE-245: disarmed live pool-group and hydration identity audit."""
import argparse
import contextlib
import io
import json
import os
import re
from collections import defaultdict
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE245_POOL_GROUP_IDENTITY.json')
B58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
SAFE_NAMES = ('address','pubkey','pool','pool_address','mint','token','token_mint',
              'base_mint','quote_mint','token_x','token_y','status','reason',
              'kind','dex','venue','program','program_id','index','active_id')


def public_attrs(obj):
    out = {}
    if isinstance(obj, dict):
        entries = obj
    else:
        entries = {}
        for name in SAFE_NAMES:
            try:
                value = getattr(obj, name)
            except Exception:
                continue
            entries[name] = value
    for name, value in entries.items():
        if name not in SAFE_NAMES:
            continue
        if isinstance(value, (int, float, bool, type(None))):
            out[name] = value
        elif isinstance(value, str) and (B58.fullmatch(value) or len(value) < 50):
            out[name] = value
        elif type(value).__name__ == 'Pubkey':
            out[name] = str(value)
    return out


def analyze(creg, pairs):
    grouped = defaultdict(list)
    failures = []
    if not isinstance(creg, dict):
        return [], ['REGISTRY_SCHEMA']
    for key, item in creg.items():
        if not isinstance(item, (list, tuple)) or len(item) != 2 or type(item[0]) is not int:
            failures.append('UNKNOWN_REGISTRY_ROW')
            continue
        group_id, pool = item
        address = str(key)
        if not B58.fullmatch(address):
            failures.append('NON_ADDRESS_REGISTRY_KEY')
            continue
        grouped[group_id].append({'address': address, 'class': type(pool).__name__,
                                  'attributes': public_attrs(pool)})
    prepared = []
    for pair in pairs:
        entry = public_attrs(pair)
        for name in ('token', 'pump_pool', 'meteora_pool'):
            try:
                entry[name] = str(getattr(pair, name))
            except Exception:
                pass
        prepared.append(entry)
    rows = []
    used = set()
    for group_id, pools in sorted(grouped.items()):
        addresses = {v['address'] for v in pools}
        matched = []
        for index, pair in enumerate(prepared):
            pair_pools = {pair.get('pump_pool'), pair.get('meteora_pool')}
            overlap = sorted(addresses & pair_pools)
            if overlap:
                matched.append({'prepared_index': index, 'token': pair.get('token'),
                                'matched_pool_addresses': overlap,
                                'full_pair_match': len(overlap) == 2})
                used.add(index)
        rows.append({'group': group_id, 'pool_count': len(pools), 'pools': pools,
                     'prepared_matches': matched,
                     'status': ('MATCHED_BOTH_POOLS' if any(m['full_pair_match'] for m in matched)
                                else 'PARTIAL_ADDRESS_MATCH' if matched else 'UNMATCHED_GROUP')})
    for index in range(len(prepared)):
        if index not in used:
            failures.append('HYDRATED_PAIR_ABSENT_FROM_REGISTRY')
    return rows, sorted(set(failures))


def test():
    class Pair:
        token = 'T' * 32
        pump_pool = 'A' * 32
        meteora_pool = 'B' * 32
    pool = {'status': 'READY'}
    registry = {'A'*32: (0, pool), 'B'*32: (0, pool),
                'C'*32: (1, pool), 'D'*32: (1, pool)}
    rows, errors = analyze(registry, [Pair()])
    assert not errors and len(rows) == 2
    assert rows[0]['status'] == 'MATCHED_BOTH_POOLS'
    assert rows[1]['status'] == 'UNMATCHED_GROUP'
    assert all(len(r['pools']) == 2 for r in rows)
    print('[ORACLE245_TEST_PASS] pool_pairs=TRUE identity_join=TRUE unmatched_hold=TRUE signing=FALSE')


def run():
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('LIVE_ARM_REFUSED')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('PRIVATE_KEY_ENV_REFUSED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as d
    original = r.q87.c.rpc
    state, error, output = {}, None, io.StringIO()
    try:
        r.q87.c.rpc = d.restricted_rpc_factory(original)
        with contextlib.redirect_stdout(output):
            state, _ = r.q25.prepare_once(Path.cwd())
            r.q25.bind_cached_state(state)
            r.install_proven_hot_math(state)
    except Exception as exc:
        error = type(exc).__name__
    finally:
        r.q87.c.rpc = original
    groups, issues = analyze(state.get('creg'), state.get('pairs') or [])
    result = {'build': 'ORACLE245', 'groups': groups, 'issues': issues,
              'prepared_pair_count': len(state.get('pairs') or []),
              'unmatched_groups': sum(x['status'] == 'UNMATCHED_GROUP' for x in groups),
              'state_diagnostic_shapes': {}, 'preparation_error': error,
              'execution_admission': False, 'signing': False, 'broadcast': False,
              'status': 'HOLD_UNMATCHED_HYDRATION_LINEAGE'}
    for name in ('cstates', 'cutover_report', 'cutover_errors', 'damm_states', 'clmm_records'):
        val = state.get(name)
        if isinstance(val, (list, tuple, dict)):
            result['state_diagnostic_shapes'][name] = {'type': type(val).__name__, 'count': len(val)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE245_RESULT]', json.dumps({
        'pool_groups': len(groups), 'prepared_pairs': result['prepared_pair_count'],
        'unmatched_groups': result['unmatched_groups'], 'issues': issues,
        'error': error, 'signing': False, 'broadcast': False}, sort_keys=True))
    for row in groups:
        print('[ORACLE245_GROUP]', json.dumps({
            'group': row['group'], 'pool_addresses': [p['address'] for p in row['pools']],
            'pool_attributes': [p['attributes'] for p in row['pools']],
            'status': row['status'], 'matches': row['prepared_matches']}, sort_keys=True))
    print('[ORACLE245_STATE]', json.dumps(result['state_diagnostic_shapes'], sort_keys=True))
    print('[REPORT]', OUT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    if not (args.test or args.run):
        ap.error('Specify --test or --run')
    if args.test:
        test()
    if args.run:
        run()