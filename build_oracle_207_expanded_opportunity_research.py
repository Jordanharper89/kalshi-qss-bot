"""ORACLE207 full standalone research runner; no executor source modifications."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE207_EXPANDED_RESEARCH.json')
TARGET_CAP = 12


def get_pair_module(r):
    q60b2 = r.q25.prepare_once.__globals__['q60b2']
    q60b = q60b2.prepare_once.__globals__['q60b']
    original = q60b.extended_prepare.__globals__['_ORIG_PREPARE']
    return original.__globals__['pd']


def admissible(rows):
    return all(not x['execution_authorized'] for x in rows) and all(
        (not x['research_eligible']) or (
            x['min_net_lamports'] is not None and
            x['min_net_lamports'] > x['assumed_cost_reserve_lamports']
        ) for x in rows
    )


def test():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as ranker,
        runtime as r,
    )
    pd = get_pair_module(r)
    assert isinstance(pd.MAX_PAIRS, int) and pd.MAX_PAIRS > 0
    sample = ranker.evaluate([
        {'direction': 'METEORA_TO_PUMP', 'start': 10_000_000,
         'local_end': 10_500_000, 'local_min_end': 10_300_000},
        {'direction': 'PUMP_TO_METEORA', 'start': 10_000_000,
         'local_end': 9_950_000},
    ], 'FIXTURE', .010)
    assert admissible(sample)
    assert sum(x['research_eligible'] for x in sample) == 1
    assert TARGET_CAP > 0 and TARGET_CAP <= 12
    print('[ORACLE207_TEST_PASS] cap_contract=%d provisional_profit_gate=TRUE broadcast=FALSE'
          % pd.MAX_PAIRS)


def research():
    if os.getenv('QSB_LIVE_ARM', '').upper() == 'YES':
        raise RuntimeError('ORACLE207_ARMED_REFUSED')

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as ranker,
        oracle186_direct_route_truth as diagnostic,
        runtime as r,
    )

    ranker.freeze()
    diagnostic.safety()

    pd = get_pair_module(r)
    initial_cap = pd.MAX_PAIRS
    if not isinstance(initial_cap, int) or not 0 < initial_cap <= 100:
        raise RuntimeError('ORACLE207_UNKNOWN_PAIR_CAP')

    old_rpc = r.q87.c.rpc
    rows, errors, paired = [], [], []

    print('[ORACLE207_CAP] original=%d research_target=%d persistent_change=FALSE'
          % (initial_cap, TARGET_CAP), flush=True)

    try:
        pd.MAX_PAIRS = max(initial_cap, TARGET_CAP)
        r.q87.c.rpc = diagnostic.restricted_rpc_factory(old_rpc)

        paired, _user = diagnostic.bootstrap()

        for pair in paired:
            token = str(pair.token)
            try:
                snap = r.immutable_snapshot(pair)
            except Exception as exc:
                errors.append({
                    'token': token[:12],
                    'stage': 'SNAPSHOT',
                    'error_type': type(exc).__name__
                })
                continue

            for size in ranker.SIZES:
                try:
                    quotes = r.q18.exact_snapshot_opportunities(snap, size)
                    rows.extend(ranker.evaluate(quotes, token, size))
                except Exception as exc:
                    errors.append({
                        'token': token[:12],
                        'size': size,
                        'stage': 'QUOTE',
                        'error_type': type(exc).__name__
                    })
    finally:
        pd.MAX_PAIRS = initial_cap
        r.q87.c.rpc = old_rpc
        w = getattr(r.q18, '_worker', None)
        if w is not None:
            try:
                w.close()
                r.q18._worker = None
            except Exception:
                pass
        ranker.freeze()
        print('[ORACLE207_CAP_RESTORED] cap=%d executor_unchanged=TRUE'
              % initial_cap, flush=True)

    if not admissible(rows):
        raise RuntimeError('ORACLE207_RESEARCH_ADMISSION_INVARIANT_FAILED')

    rows.sort(
        key=lambda x: (
            x['research_eligible'],
            x['min_net_lamports']
            if x['min_net_lamports'] is not None else -10**18,
            x['estimated_net_lamports']
        ),
        reverse=True
    )

    count = sum(x['research_eligible'] for x in rows)

    report = {
        'build': 'ORACLE207',
        'status': 'RESEARCH_ONLY',
        'original_max_pairs': initial_cap,
        'temporary_target_max_pairs': TARGET_CAP,
        'prepared_pairs': len(paired),
        'evaluated_quotes': len(rows),
        'provisional_positive': count,
        'pairs': [{'token': str(p.token)[:12]} for p in paired],
        'rows': rows,
        'errors': errors,
        'cost_reserve_provisional': True,
        'freshness_certified': False,
        'atomic_simulation_certified': False,
        'execution_authorized': False,
        'signing': False,
        'broadcast': False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')

    print(
        '[ORACLE207_RANK] pairs=%d quotes=%d provisional_positive=%d broadcast=FALSE'
        % (len(paired), len(rows), count),
        flush=True
    )

    for row in rows[:12]:
        print(
            '[ORACLE207_CANDIDATE] token=%s direction=%s size=%.3f '
            'net=%d min_net=%s status=%s'
            % (
                row['token'],
                row['direction'],
                row['size_sol'],
                row['estimated_net_lamports'],
                row['min_net_lamports'],
                'RESEARCH_ONLY' if row['research_eligible'] else 'HOLD'
            ),
            flush=True
        )

    print('[ORACLE207_REPORT]', OUT, flush=True)


def launch():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as ranker,
    )
    ranker.freeze()

    import build_oracle_182_secure_windows_credentials as vault
    db = vault.api()
    h = vault.load(db, vault.HELIUS)
    k = vault.load(db, vault.SOLANA)

    if not h or not k:
        raise RuntimeError('ORACLE207_CREDENTIALS_MISSING')

    env = os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY'] = k
    env['SOLANA_RPC_URL'] = (
        'https://mainnet.helius-rpc.com/?api-key='
        + vault.quote(h, safe='')
    )
    env['SOLANA_WS_URL'] = (
        'wss://mainnet.helius-rpc.com/?api-key='
        + vault.quote(h, safe='')
    )
    env['QSB_LIVE_ARM'] = 'NO'

    return subprocess.call(
        [sys.executable, __file__, '--worker'],
        env=env
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test', action='store_true')
    group.add_argument('--run', action='store_true')
    group.add_argument('--worker', action='store_true')
    args = parser.parse_args()

    if args.test:
        test()
    elif args.run:
        sys.exit(launch())
    else:
        research()