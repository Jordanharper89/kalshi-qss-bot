"""ORACLE-249: expanded exact-pair gross-size research. No wallet or trades."""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE249_EXPANDED_RAW.json'
OUT = ROOT / 'ORACLE249_EXPANDED_PRICING.json'
SIZES = tuple(x / 1000 for x in range(10, 101, 5))
DIRECTIONS = {'PUMP_TO_METEORA', 'METEORA_TO_PUMP'}


def rank(source):
    rows, holds = [], Counter()
    if source.get('build') != 'ORACLE241' or source.get('signing') is not False \
            or source.get('broadcast') is not False \
            or source.get('execution_admission') is not False:
        raise ValueError('UNTRUSTED_SOURCE')

    for obs in source.get('observations', []):
        if not isinstance(obs, dict):
            holds['BAD_ROW'] += 1
            continue

        if obs.get('status') != 'FULL_FILL_GROSS_MEASURED':
            holds[str(obs.get('status', 'UNKNOWN'))] += 1
            continue

        size = obs.get('size_sol')
        if type(size) not in (int, float) or not any(
                abs(size - x) < 1e-9 for x in SIZES):
            holds['INVALID_SIZE'] += 1
            continue

        start = round(size * 1_000_000_000)
        qs = obs.get('directions')

        if not isinstance(qs, list) or len(qs) != 2 or any(
                not isinstance(q, dict) for q in qs):
            holds['BAD_DIRECTIONS'] += 1
            continue

        if {q.get('direction') for q in qs} != DIRECTIONS:
            holds['BAD_DIRECTIONS'] += 1
            continue

        if any(
            type(q.get('start_lamports')) is not int
            or q['start_lamports'] != start
            or type(q.get('end_lamports')) is not int
            or q['end_lamports'] <= 0
            or type(q.get('gross_lamports')) is not int
            or q['gross_lamports'] != q['end_lamports'] - start
            for q in qs
        ):
            holds['BAD_ACCOUNTING'] += 1
            continue

        mint = obs.get('mint')
        if not isinstance(mint, str) or len(mint) < 32:
            holds['BAD_IDENTITY'] += 1
            continue

        for q in qs:
            rows.append({
                'token_prefix': mint[:12],
                'cycle': obs.get('cycle'),
                'size_sol': size,
                'direction': q['direction'],
                'gross_lamports': q['gross_lamports'],
                'gross_bps': round(
                    q['gross_lamports'] * 10000 / start, 4
                ),
                'fee_adjusted': False,
                'execution_admission': False
            })

    rows.sort(
        key=lambda x: x['gross_lamports'],
        reverse=True
    )
    return rows, dict(holds)


def test():
    assert len(SIZES) == 19
    assert SIZES[0] == .01
    assert SIZES[-1] == .1

    q = [{
        'direction': d,
        'start_lamports': 10_000_000,
        'end_lamports': 10_002_000,
        'gross_lamports': 2000
    } for d in sorted(DIRECTIONS)]

    source = {
        'build': 'ORACLE241',
        'signing': False,
        'broadcast': False,
        'execution_admission': False,
        'observations': [{
            'mint': 'A' * 44,
            'size_sol': .01,
            'cycle': 1,
            'status': 'FULL_FILL_GROSS_MEASURED',
            'directions': q
        }]
    }

    rows, issues = rank(source)
    assert len(rows) == 2
    assert not issues
    assert rows[0]['gross_lamports'] == 2000

    q[0]['gross_lamports'] = 2001
    assert not rank(source)[0]
    assert rank(source)[1]['BAD_ACCOUNTING'] == 1

    print(
        '[ORACLE249_TEST_PASS] '
        '19_sizes=TRUE directions=TRUE '
        'accounting=TRUE disarmed=TRUE'
    )


def run(cycles, target, gap):
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('ARMED_ENV_REFUSED')

    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('PRIVATE_KEY_PRESENT_REFUSED')

    if not os.getenv(
        'SOLANA_RPC_URL', ''
    ).startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')

    import build_oracle_241_live_opportunity_sampler as sampler

    from qseries_v2.oracle_strategy_intelligence.solana_money \
        .qarb_clean_bot import live_account_stream as pd

    g = pd.prepare_pairs.__globals__

    previous_cap = g.get('MAX_PAIRS')
    previous_sizes = sampler.SIZES
    previous_out = sampler.OUT

    if type(previous_cap) is not int or not 1 <= previous_cap <= 100:
        raise RuntimeError('CAP_NOT_VERIFIED')

    if not callable(sampler.run) or not callable(sampler.inspect):
        raise RuntimeError('SAMPLER_UNAVAILABLE')

    if RAW.exists():
        RAW.unlink()

    try:
        g['MAX_PAIRS'] = max(previous_cap, target)
        sampler.SIZES = SIZES
        sampler.OUT = RAW

        sampler.run(cycles, target, gap)

    finally:
        g['MAX_PAIRS'] = previous_cap
        sampler.SIZES = previous_sizes
        sampler.OUT = previous_out

    if not RAW.is_file():
        raise RuntimeError('NO_LIVE_SAMPLER_REPORT')

    source = json.loads(
        RAW.read_text(encoding='utf-8')
    )

    rows, holds = rank(source)
    positives = [
        r for r in rows
        if r['gross_lamports'] > 0
    ]

    result = {
        'build': 'ORACLE249',
        'configured_cap_restored':
            g['MAX_PAIRS'] == previous_cap,
        'research_cap': max(previous_cap, target),
        'cycles': len(source.get('cycles', [])),
        'sizes': len(SIZES),
        'sample_attempts': len(
            source.get('observations', [])
        ),
        'unique_priced_tokens': len({
            r['token_prefix'] for r in rows
        }),
        'full_fill_direction_samples': len(rows),
        'positive_gross_directions': len(positives),
        'holds': holds,
        'best_observations': rows[:20],
        'net_profit_certified': False,
        'synchronized_account_state_certified': False,
        'atomic_simulation_certified': False,
        'execution_admission': False,
        'signing': False,
        'broadcast': False,
        'status': 'HOLD_NET_AND_ATOMIC_CERTIFICATION'
    }

    OUT.parent.mkdir(
        parents=True, exist_ok=True
    )
    OUT.write_text(
        json.dumps(result, indent=2),
        encoding='utf-8'
    )

    print(
        '[ORACLE249_RESULT]',
        json.dumps({
            k: v for k, v in result.items()
            if k != 'best_observations'
        }, sort_keys=True)
    )

    for row in rows[:10]:
        print(
            '[ORACLE249_TOP_GROSS]',
            json.dumps(row, sort_keys=True)
        )

    print('[REPORT]', OUT)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    p.add_argument('--cycles', type=int, default=2)
    p.add_argument('--target', type=int, default=12)
    p.add_argument('--gap', type=int, default=5)

    a = p.parse_args()

    if not (a.test or a.run):
        p.error('use --test or --run')

    if a.test:
        test()

    if a.run:
        run(
            max(1, min(a.cycles, 5)),
            max(4, min(a.target, 20)),
            max(0, min(a.gap, 30))
        )