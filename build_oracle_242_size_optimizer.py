"""ORACLE-242: 0.010-0.100 SOL canonical gross-size research. No trades."""
import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE242_LIVE_SIZE_SAMPLES.json'
REPORT = ROOT / 'ORACLE242_SIZE_OPTIMIZATION.json'
SIZES = tuple(n / 1000 for n in range(10, 101, 5))


def analyze(observations):
    grouped = defaultdict(list)

    for row in observations:
        if not isinstance(row, dict):
            continue
        size = row.get('size_sol')
        if type(size) not in (float, int):
            continue
        if not any(abs(size - s) < 1e-9 for s in SIZES):
            continue
        grouped[round(size, 3)].append(row)

    rows, candidates = [], []

    for size in SIZES:
        attempts = grouped[round(size, 3)]
        measured, holds, winners = 0, Counter(), []

        for item in attempts:
            if item.get('status') != 'FULL_FILL_GROSS_MEASURED':
                holds[str(item.get('status', 'UNKNOWN'))] += 1
                continue

            quotes = item.get('directions')
            start = round(size * 1_000_000_000)

            if not isinstance(quotes, list) or len(quotes) != 2:
                holds['INVALID_DIRECTIONS'] += 1
                continue

            if any(not isinstance(q, dict) for q in quotes):
                holds['INVALID_DIRECTIONS'] += 1
                continue

            expected = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}
            if {q.get('direction') for q in quotes} != expected:
                holds['INVALID_DIRECTIONS'] += 1
                continue

            if any(
                type(q.get('start_lamports')) is not int
                or q['start_lamports'] != start
                or type(q.get('gross_lamports')) is not int
                or type(q.get('end_lamports')) is not int
                or q['end_lamports'] - start != q['gross_lamports']
                for q in quotes
            ):
                holds['INVALID_AMOUNT_ACCOUNTING'] += 1
                continue

            measured += 1
            best = max(quotes, key=lambda q: q['gross_lamports'])

            if best['gross_lamports'] > 0:
                candidate = {
                    'mint': item.get('mint'),
                    'cycle': item.get('cycle'),
                    'size_sol': size,
                    'direction': best['direction'],
                    'gross_lamports': best['gross_lamports'],
                    'gross_bps': best['gross_lamports'] * 10000 / start,
                    'maximum_theoretical_cost_lamports':
                        best['gross_lamports'],
                    'net_certified': False,
                    'execution_admission': False
                }
                winners.append(candidate)
                candidates.append(candidate)

        rows.append({
            'size_sol': size,
            'attempts': len(attempts),
            'full_fill_samples': measured,
            'positive_gross_samples': len(winners),
            'holds': dict(holds),
            'best_gross_lamports': max(
                (x['gross_lamports'] for x in winners),
                default=None
            ),
            'net_profit_certified': False
        })

    candidates.sort(
        key=lambda x: x['gross_lamports'],
        reverse=True
    )
    return rows, candidates


def test():
    assert len(SIZES) == 19
    assert SIZES[0] == .01
    assert SIZES[-1] == .1

    samples = [{
        'cycle': 1,
        'mint': 'test',
        'size_sol': .01,
        'status': 'FULL_FILL_GROSS_MEASURED',
        'directions': [{
            'direction': d,
            'start_lamports': 10_000_000,
            'end_lamports': 10_000_050,
            'gross_lamports': 50
        } for d in ('PUMP_TO_METEORA', 'METEORA_TO_PUMP')]
    }, {
        'size_sol': .015,
        'status': 'HOLD_QUOTE_RuntimeError'
    }]

    rows, candidates = analyze(samples)
    assert len(rows) == 19
    assert len(candidates) == 1
    assert candidates[0]['maximum_theoretical_cost_lamports'] == 50
    assert candidates[0]['execution_admission'] is False

    samples[0]['directions'][0]['gross_lamports'] = 51
    assert not analyze(samples)[1]

    samples[0]['directions'][0]['gross_lamports'] = 50
    for q in samples[0]['directions']:
        q['end_lamports'] = 9_999_950
        q['gross_lamports'] = -50

    assert not analyze(samples)[1]

    print(
        '[ORACLE242_TEST_PASS] '
        '19_sizes=TRUE accounting=TRUE '
        'holds=TRUE no_execution=TRUE'
    )


def run(cycles, pairs, gap):
    if os.environ.get('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('HOLD_ARMED_ENVIRONMENT')
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_PRESENT')
    if not os.environ.get('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('HOLD_RPC_MISSING')

    import build_oracle_241_live_opportunity_sampler as sampler

    if not callable(sampler.run) or not callable(sampler.inspect):
        raise RuntimeError('HOLD_CANONICAL_SAMPLER_MISSING')

    ROOT.mkdir(parents=True, exist_ok=True)
    original_sizes, original_out = sampler.SIZES, sampler.OUT

    try:
        sampler.SIZES = SIZES
        sampler.OUT = RAW
        sampler.run(cycles, pairs, gap)
    finally:
        sampler.SIZES, sampler.OUT = original_sizes, original_out

    source = json.loads(RAW.read_text(encoding='utf-8'))

    if (
        source.get('build') != 'ORACLE241'
        or source.get('signing') is not False
        or source.get('broadcast') is not False
    ):
        raise RuntimeError('HOLD_SOURCE_INTEGRITY')

    rows, candidates = analyze(source.get('observations', []))

    result = {
        'build': 'ORACLE242',
        'size_count': len(SIZES),
        'cycles': cycles,
        'total_samples': len(source.get('observations', [])),
        'gross_positive_samples': len(candidates),
        'by_size': rows,
        'top_gross_observations': candidates[:15],
        'fee_adjusted_profit_proven': False,
        'same_context_execution_state_proven': False,
        'signed_atomic_simulation_proven': False,
        'execution_admission': False,
        'signing': False,
        'broadcast': False,
        'status': 'HOLD_NET_AND_ATOMIC_CERTIFICATION'
    }

    REPORT.write_text(
        json.dumps(result, indent=2),
        encoding='utf-8'
    )

    for item in rows:
        print('[ORACLE242_SIZE]', json.dumps(
            {k: v for k, v in item.items() if k != 'holds'},
            sort_keys=True
        ))

    print('[ORACLE242_RESULT]', json.dumps(
        {
            k: v for k, v in result.items()
            if k not in ('by_size', 'top_gross_observations')
        },
        sort_keys=True
    ))

    for item in candidates[:10]:
        print(
            '[ORACLE242_POSITIVE_GROSS_ONLY]',
            json.dumps(item, sort_keys=True)
        )

    print('[REPORT]', REPORT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--cycles', type=int, default=3)
    ap.add_argument('--pairs', type=int, default=12)
    ap.add_argument('--gap', type=int, default=8)
    args = ap.parse_args()

    if not args.test and not args.run:
        ap.error('specify --test or --run')

    if args.test:
        test()

    if args.run:
        run(
            max(1, min(args.cycles, 5)),
            max(1, min(args.pairs, 30)),
            max(0, min(args.gap, 30))
        )