"""ORACLE216 complete offline zero-fill reconciliation; no RPC or execution."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

STATE = Path('runtime_state/oracle/oracle_live_execution')
SOURCE = STATE / 'ORACLE213_DLMM_PARTIAL_EVIDENCE.json'
OUT = STATE / 'ORACLE216_ZERO_FILL_RECONCILIATION.json'


def reconcile(data):
    if data.get('build') != 'ORACLE213' or data.get('broadcast') is not False:
        raise ValueError('ORACLE216_INVALID_SOURCE')

    calls = data.get('captured_dlmm_calls')
    if not isinstance(calls, list):
        raise ValueError('ORACLE216_CALLS_MISSING')

    issues, counts = [], Counter()
    per_token = defaultdict(
        lambda: {'calls': 0, 'zero_fills': 0, 'partials': 0}
    )

    for row in calls:
        token = str(row.get('token') or 'UNKNOWN')[:12]
        per_token[token]['calls'] += 1

        req = row.get('requested_raw')
        rem = row.get('remaining_raw')

        if not isinstance(req, int) or req <= 0 or not isinstance(rem, int):
            counts['NO_QUANTITY_EVIDENCE'] += 1
            continue

        if rem < 0 or rem > req:
            counts['INVALID_QUANTITY'] += 1
            issues.append({
                'token': token,
                'size_sol': row.get('size_sol'),
                'classification': 'INVALID_QUANTITY'
            })
            continue

        if rem == req:
            code = 'ZERO_FILL'
            per_token[token]['zero_fills'] += 1
        elif rem > 0:
            code = 'PARTIAL_FILL'
            per_token[token]['partials'] += 1
        else:
            code = 'INPUT_CONSUMED'

        counts[code] += 1

        if code != 'INPUT_CONSUMED':
            issues.append({
                'token': token,
                'size_sol': row.get('size_sol'),
                'input_raw': req,
                'remaining_raw': rem,
                'complete_flag': row.get('complete'),
                'swap_for_y': row.get('swap_for_y'),
                'bins_crossed': row.get('bins_crossed'),
                'classification': code
            })

    return {
        'build': 'ORACLE216',
        'source': SOURCE.name,
        'captured_calls': len(calls),
        'counts': dict(counts),
        'per_token': dict(sorted(per_token.items())),
        'incomplete_calls': issues,
        'zero_fill_proven': counts['ZERO_FILL'] > 0,
        'missing_bin_arrays_proven': False,
        'empty_liquidity_proven': False,
        'explanation': (
            'Zero fill alone cannot distinguish absent liquidity '
            'from missing bin coverage.'
        ),
        'rpc': False,
        'signing': False,
        'broadcast': False
    }


def test():
    rows = [
        {
            'token': 'A',
            'requested_raw': 100,
            'remaining_raw': 100,
            'complete': True,
            'swap_for_y': False
        },
        {
            'token': 'B',
            'requested_raw': 100,
            'remaining_raw': 0,
            'complete': True
        },
        {
            'token': 'C',
            'requested_raw': 100,
            'remaining_raw': 40,
            'complete': False
        }
    ]

    result = reconcile({
        'build': 'ORACLE213',
        'broadcast': False,
        'captured_dlmm_calls': rows
    })

    assert result['counts'] == {
        'ZERO_FILL': 1,
        'INPUT_CONSUMED': 1,
        'PARTIAL_FILL': 1
    }
    assert result['per_token']['A']['zero_fills'] == 1
    assert result['missing_bin_arrays_proven'] is False

    print(
        '[ORACLE216_TEST_PASS] '
        'completion_flag_independent=TRUE offline=TRUE'
    )


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze
    )

    freeze.freeze()

    result = reconcile(
        json.loads(SOURCE.read_text(encoding='utf-8'))
    )

    if result['counts'].get('INVALID_QUANTITY'):
        raise RuntimeError('ORACLE216_INVALID_QUOTE_QUANTITIES')

    STATE.mkdir(parents=True, exist_ok=True)

    OUT.write_text(
        json.dumps(result, indent=2),
        encoding='utf-8'
    )

    print(
        '[ORACLE216_RESULT] calls=%d classification=%s'
        % (result['captured_calls'], result['counts'])
    )

    for token, row in result['per_token'].items():
        if row['zero_fills'] or row['partials']:
            print(
                '[ORACLE216_TOKEN] token=%s calls=%d '
                'zero_fills=%d partials=%d'
                % (
                    token,
                    row['calls'],
                    row['zero_fills'],
                    row['partials']
                )
            )

    print(
        '[ORACLE216_DECISION] '
        'missing_bin_arrays=UNPROVEN empty_liquidity=UNPROVEN'
    )
    print('[REPORT]', OUT)

    freeze.freeze()

    print(
        '[ORACLE216_PASS] executor_unchanged=TRUE '
        'rpc=FALSE signing=FALSE broadcast=FALSE'
    )


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test', action='store_true')
    g.add_argument('--run', action='store_true')

    a = p.parse_args()

    if a.test:
        test()
    else:
        run()