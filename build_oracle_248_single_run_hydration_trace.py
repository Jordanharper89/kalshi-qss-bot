"""ORACLE-248: single-run, read-only atomic hydration admission trace."""
import argparse
import contextlib
import io
import json
import os
from collections import Counter
from pathlib import Path

OUT = Path(
    'runtime_state/oracle/oracle_live_execution/'
    'ORACLE248_SINGLE_RUN_HYDRATION.json'
)


def identity(x):
    if isinstance(x, dict):
        value = x.get('token') or x.get('mint')
    else:
        value = getattr(x, 'token', None)
    return str(value) if value is not None else None


def summarize(universe, pairs, calls, cap):
    candidates = [identity(x) for x in universe]
    prepared = [identity(x) for x in pairs]
    counts = Counter(c for c in candidates if c)
    missed = [
        c for c in candidates
        if c and c not in prepared
    ]
    return {
        'trial_cap': cap,
        'candidate_count': len(universe),
        'candidate_tokens_resolved': sum(
            bool(c) for c in candidates
        ),
        'candidate_duplicate_tokens': sum(
            n - 1 for n in counts.values() if n > 1
        ),
        'prepared_count': len(pairs),
        'prepared_tokens': [
            p[:12] if p else None for p in prepared
        ],
        'unprepared_candidate_count': len(missed),
        'unprepared_token_prefixes': [
            m[:12] for m in missed
        ],
        'stage_calls': calls,
        'candidate_to_pair_identity_is_not_causal_proof': True,
        'execution_admission': False,
        'signing': False,
        'broadcast': False,
    }


def test():
    u = [
        {'token': 'A' * 32},
        {'token': 'B' * 32},
        {'token': 'C' * 32},
    ]
    p = [
        type('P', (), {'token': 'A' * 32})()
    ]
    row = summarize(
        u, p, {'discover_dlmm': {'calls': 3}}, 12
    )
    assert row['candidate_count'] == 3
    assert row['prepared_count'] == 1
    assert row['unprepared_candidate_count'] == 2
    assert row['signing'] is False
    assert row['broadcast'] is False
    print(
        '[ORACLE248_TEST_PASS] '
        'single_run_join=TRUE cap=TRUE disarmed=TRUE'
    )


def run(target):
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('ARMED_ENV_REFUSED')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('PRIVATE_KEY_PRESENT_REFUSED')
    if not os.getenv(
        'SOLANA_RPC_URL', ''
    ).startswith('https://'):
        raise RuntimeError('RPC_REQUIRED')

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as guard
    from qseries_v2.oracle_strategy_intelligence.solana_money \
        .qarb_clean_bot import live_account_stream as pd

    fn = pd.prepare_pairs
    globals_ = fn.__globals__
    prior_cap = globals_.get('MAX_PAIRS')

    if type(prior_cap) is not int or not 1 <= prior_cap <= 100:
        raise RuntimeError('UNSAFE_CAP_BINDING')
    if r.q87.c is not pd.c:
        raise RuntimeError('RPC_GUARD_IDENTITY_MISMATCH')
    if (
        'engine' not in globals_
        or not hasattr(
            globals_['engine'], 'candidate_universe'
        )
    ):
        raise RuntimeError('CANDIDATE_PRODUCER_NOT_FOUND')

    engine = globals_['engine']
    previous_producer = engine.candidate_universe
    previous_rpc = r.q87.c.rpc

    originals = {}
    candidates = []
    pairs = []
    error_types = []
    stages = {}
    captured = io.StringIO()

    def producer(*args, **kwargs):
        result = previous_producer(*args, **kwargs)
        if isinstance(result, (list, tuple)):
            candidates.extend(result)
        else:
            error_types.append(
                'CANDIDATE_UNIVERSE_NOT_SEQUENCE'
            )
        return result

    def wrap(name, original):
        def observe(*args, **kwargs):
            bucket = stages.setdefault(
                name, {
                    'calls': 0,
                    'successes': 0,
                    'errors': {},
                }
            )
            bucket['calls'] += 1
            try:
                result = original(*args, **kwargs)
                bucket['successes'] += 1
                return result
            except Exception as exc:
                kind = type(exc).__name__
                bucket['errors'][kind] = (
                    bucket['errors'].get(kind, 0) + 1
                )
                raise
        return observe

    try:
        r.q87.c.rpc = guard.restricted_rpc_factory(
            previous_rpc
        )

        globals_['MAX_PAIRS'] = max(
            prior_cap, target
        )
        engine.candidate_universe = producer

        for owner, name in (
            (pd.c, 'discover_dlmm'),
            (pd.c, 'dlmm_arrays'),
            (pd, '_build_dlmm_state'),
        ):
            original = getattr(owner, name, None)
            if callable(original):
                originals[(owner, name)] = original
                setattr(
                    owner, name,
                    wrap(name, original)
                )

        with contextlib.redirect_stdout(captured):
            pairs, _ = fn(Path.cwd())

    except Exception as exc:
        error_types.append(type(exc).__name__)

    finally:
        for (owner, name), original in originals.items():
            setattr(owner, name, original)

        engine.candidate_universe = previous_producer
        globals_['MAX_PAIRS'] = prior_cap
        r.q87.c.rpc = previous_rpc

    row = summarize(
        candidates,
        pairs,
        stages,
        max(prior_cap, target),
    )

    row.update({
        'build': 'ORACLE248',
        'original_cap_restored':
            globals_['MAX_PAIRS'] == prior_cap,
        'errors': error_types,
        'prepared_pairs': [
            {
                'token_prefix': str(
                    getattr(p, 'token', '')
                )[:12],
                'pump_prefix': str(
                    getattr(p, 'pump_pool', '')
                )[:12],
                'meteora_prefix': str(
                    getattr(p, 'meteora_pool', '')
                )[:12],
            }
            for p in pairs
        ],
        'status':
            'HOLD_LIVE_PRICING_AND_EXECUTION_NOT_CERTIFIED',
    })

    OUT.parent.mkdir(
        parents=True, exist_ok=True
    )
    OUT.write_text(
        json.dumps(row, indent=2),
        encoding='utf-8'
    )

    print(
        '[ORACLE248_RESULT]',
        json.dumps({
            'candidate_count': row['candidate_count'],
            'prepared_count': row['prepared_count'],
            'unprepared_count':
                row['unprepared_candidate_count'],
            'stage_calls': row['stage_calls'],
            'errors': error_types,
            'original_cap_restored':
                row['original_cap_restored'],
            'signing': False,
            'broadcast': False,
        }, sort_keys=True)
    )
    print(
        '[ORACLE248_MISSED]',
        json.dumps(
            row['unprepared_token_prefixes']
        )
    )
    print(
        '[ORACLE248_PREPARED]',
        json.dumps(row['prepared_pairs'])
    )
    print('[REPORT]', OUT)

    if error_types:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test', action='store_true'
    )
    parser.add_argument(
        '--run', action='store_true'
    )
    parser.add_argument(
        '--target', type=int, default=12
    )

    args = parser.parse_args()
    if not (args.test or args.run):
        parser.error('Specify --test or --run')

    if args.test:
        test()

    if args.run:
        run(max(1, min(args.target, 30)))