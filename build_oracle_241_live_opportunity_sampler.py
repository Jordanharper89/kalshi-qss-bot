"""ORACLE-241: disarmed live, exact bidirectional opportunity sampling."""
import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
OUT = ROOT / 'ORACLE241_LIVE_OPPORTUNITY_SAMPLES.json'
SIZES = (0.010, 0.015, 0.025)
DIRECTIONS = {'METEORA_TO_PUMP', 'PUMP_TO_METEORA'}


def inspect(quotes, fills, size):
    start = int(round(size * 1_000_000_000))
    if not isinstance(quotes, (tuple, list)) or len(quotes) != 2:
        return 'HOLD_MISSING_DIRECTIONS', []
    if any(not isinstance(q, dict) for q in quotes):
        return 'HOLD_QUOTE_SCHEMA', []
    if {q.get('direction') for q in quotes} != DIRECTIONS:
        return 'HOLD_DIRECTION_MISMATCH', []
    if len(fills) != 2 or any(
        not f.get('complete')
        or type(f.get('remaining_in')) is not int
        or f['remaining_in'] != 0
        for f in fills
    ):
        return 'HOLD_PARTIAL_DLMM', []
    rows = []
    for q in quotes:
        end, net = q.get('local_end'), q.get('local_net')
        if (
            type(end) is not int
            or type(net) is not int
            or end <= 0
            or net != end - start
            or q.get('start') != start
        ):
            return 'HOLD_AMOUNT_INCONSISTENT', []
        rows.append({
            'direction': q['direction'],
            'start_lamports': start,
            'end_lamports': end,
            'gross_lamports': net,
            'gross_bps': round(net * 10000 / start, 5)
        })
    return 'FULL_FILL_GROSS_MEASURED', rows


def test():
    def q(d):
        return {
            'direction': d,
            'start': 10_000_000,
            'local_end': 10_002_000,
            'local_net': 2000
        }

    good = [q(d) for d in sorted(DIRECTIONS)]
    fills = [
        {'complete': True, 'remaining_in': 0}
        for _ in range(2)
    ]
    assert inspect(good, fills, .010)[0] == (
        'FULL_FILL_GROSS_MEASURED'
    )
    assert inspect(good, fills[:1], .010)[0] == (
        'HOLD_PARTIAL_DLMM'
    )
    partial = [
        {'complete': True, 'remaining_in': 1},
        fills[1]
    ]
    assert inspect(good, partial, .010)[0] == (
        'HOLD_PARTIAL_DLMM'
    )
    wrong = [dict(x) for x in good]
    wrong[0]['local_net'] = 100
    assert inspect(wrong, fills, .010)[0] == (
        'HOLD_AMOUNT_INCONSISTENT'
    )
    print(
        '[ORACLE241_TEST_PASS] full_fill=TRUE '
        'both_directions=TRUE partial_rejected=TRUE '
        'net_math=TRUE execution=FALSE'
    )


def run(cycles, limit, gap):
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('HOLD_LIVE_ARM_NOT_NO')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_IN_PROCESS')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('HOLD_NO_READ_ONLY_RPC')

    import meteora_dlmm
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as guard

    report = {
        'build': 'ORACLE241',
        'research_only': True,
        'signing': False,
        'broadcast': False,
        'execution_admission': False,
        'fee_adjusted_profit_certified': False,
        'same_context_lineage_certified': False,
        'mriya_attribution_certified': False,
        'sizes_sol': list(SIZES),
        'observations': [],
        'cycles': [],
        'started_at': datetime.now(timezone.utc).isoformat()
    }

    old_rpc = r.q87.c.rpc
    old_dlmm = meteora_dlmm.quote
    active = []

    def traced_dlmm(*args, **kwargs):
        try:
            value = old_dlmm(*args, **kwargs)
            rem = (
                value.get('remaining_in')
                if isinstance(value, dict)
                else getattr(value, 'remaining_in', None)
            )
            full = (
                value.get('complete')
                if isinstance(value, dict)
                else getattr(value, 'complete', None)
            )
            active.append({
                'complete': full is True,
                'remaining_in': (
                    rem if type(rem) is int else None
                )
            })
            return value
        except Exception:
            active.append({
                'complete': False,
                'remaining_in': None
            })
            raise

    try:
        r.q87.c.rpc = guard.restricted_rpc_factory(old_rpc)
        meteora_dlmm.quote = traced_dlmm

        for cycle in range(cycles):
            record = {
                'cycle': cycle + 1,
                'prepared_pairs': 0,
                'outcomes': {}
            }
            counter = Counter()

            try:
                state, _ = r.q25.prepare_once(Path.cwd())
                r.q25.bind_cached_state(state)
                r.install_proven_hot_math(state)
                pairs = list(state.get('pairs') or [])[:limit]
                record['prepared_pairs'] = len(pairs)

                for pair in pairs:
                    mint = str(pair.token)
                    try:
                        r.q18.worker().warm(str(pair.pump_pool))
                        snap = r.immutable_snapshot(pair)
                    except Exception as exc:
                        counter[
                            'HOLD_PREPARE_' + type(exc).__name__
                        ] += 1
                        continue

                    for size in SIZES:
                        active.clear()
                        row = {
                            'cycle': cycle + 1,
                            'mint': mint,
                            'pump_pool': str(pair.pump_pool),
                            'meteora_pool': str(pair.meteora_pool),
                            'size_sol': size,
                            'sampled_at': datetime.now(
                                timezone.utc
                            ).isoformat(),
                            'gross_only': True,
                            'execution_admission': False
                        }

                        try:
                            quotes = (
                                r.q18.exact_snapshot_opportunities(
                                    snap, size
                                )
                            )
                            label, values = inspect(
                                quotes, active, size
                            )
                            row['status'] = label
                            row['directions'] = values
                        except Exception as exc:
                            row['status'] = (
                                'HOLD_QUOTE_' + type(exc).__name__
                            )
                            row['exception_code'] = (
                                str(exc)
                                if str(exc) in (
                                    'DLMM_PARTIAL',
                                    'DLMM_DIRECTION',
                                    'REVERSE_TOKEN_NET_ZERO',
                                    'FORWARD_TOKEN_NET_ZERO'
                                )
                                else 'UNCLASSIFIED'
                            )

                        row['dlmm_calls'] = list(active)
                        report['observations'].append(row)
                        counter[row['status']] += 1

                        if row['status'] == (
                            'FULL_FILL_GROSS_MEASURED'
                        ):
                            best = max(
                                row['directions'],
                                key=lambda x: x['gross_lamports']
                            )
                            print(
                                '[ORACLE241_QUOTE] '
                                'token=%s size=%.3f '
                                'direction=%s gross_lamports=%d '
                                'net_certified=FALSE'
                                % (
                                    mint[:12],
                                    size,
                                    best['direction'],
                                    best['gross_lamports']
                                ),
                                flush=True
                            )

            except Exception as exc:
                record['error'] = (
                    'PREPARATION_' + type(exc).__name__
                )

            record['outcomes'] = dict(counter)
            report['cycles'].append(record)
            print(
                '[ORACLE241_CYCLE]',
                json.dumps(record, sort_keys=True),
                flush=True
            )

            if cycle + 1 < cycles:
                time.sleep(gap)

    finally:
        meteora_dlmm.quote = old_dlmm
        r.q87.c.rpc = old_rpc

        positives = [
            v
            for row in report['observations']
            if row.get('status') == 'FULL_FILL_GROSS_MEASURED'
            for v in row.get('directions', [])
            if v['gross_lamports'] > 0
        ]

        report['gross_positive_direction_samples'] = (
            len(positives)
        )
        report['status'] = (
            'HOLD_CURRENT_STATE_AND_NET_EXECUTION_CERTIFICATION'
        )
        report['finished_at'] = datetime.now(
            timezone.utc
        ).isoformat()

        ROOT.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            json.dumps(report, indent=2),
            encoding='utf-8'
        )

        print('[ORACLE241_RESULT]', json.dumps({
            'cycles': len(report['cycles']),
            'samples': len(report['observations']),
            'gross_positive_direction_samples': len(positives),
            'execution_admission': False,
            'signing': False,
            'broadcast': False,
            'status': report['status']
        }, sort_keys=True))
        print('[REPORT]', OUT)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    p.add_argument('--cycles', type=int, default=3)
    p.add_argument('--pairs', type=int, default=12)
    p.add_argument('--gap', type=int, default=8)
    a = p.parse_args()

    if not (a.test or a.run):
        p.error('Specify --test or --run')
    if a.test:
        test()
    if a.run:
        run(
            max(1, min(a.cycles, 5)),
            max(1, min(a.pairs, 30)),
            max(0, min(a.gap, 30))
        )