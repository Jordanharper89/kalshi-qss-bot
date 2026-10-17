"""ORACLE-243: one-shot, read-only discovery-to-hydration boundary audit."""
import argparse
import ast
import contextlib
import inspect
import io
import json
import os
import re
from collections import Counter
from pathlib import Path

OUT = Path(
    'runtime_state/oracle/oracle_live_execution/'
    'ORACLE243_HYDRATION_BOUNDARY.json'
)

DISCOVERY = re.compile(
    r'\[CROSSLIST_DISCOVERY\]\s+raw=(\d+)'
    r'\s+exact_pairs=(\d+)\s+failures=(\{[^\n]*\})'
)
WARM = re.compile(
    r'\[ORACLE025_TOKEN_WARM\]\s+token=([A-Za-z0-9]+)'
)


def normalize_pair(pair):
    fields = (
        'token', 'pump_pool', 'meteora_pool',
        'token_x', 'token_y',
        'pump_base_vault', 'pump_quote_vault'
    )
    found = {}
    for name in fields:
        try:
            value = getattr(pair, name, None)
            if value is not None:
                found[name] = str(value)
        except Exception:
            pass
    return found


def source_filters(func):
    """Find selection conditions in the actual preparation function."""
    try:
        lines, start = inspect.getsourcelines(func)
        tree = ast.parse(''.join(lines))
    except (OSError, TypeError, SyntaxError):
        return []

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While)):
            cond = node.test
        elif isinstance(
            node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)
        ):
            for comp in node.generators:
                for cond in comp.ifs:
                    results.append({
                        'line': start + cond.lineno - 1,
                        'test': ast.unparse(cond)[:180]
                    })
            continue
        else:
            continue

        results.append({
            'line': start + node.lineno - 1,
            'test': ast.unparse(cond)[:180]
        })

    return sorted(
        results, key=lambda item: item['line']
    )[:80]


def describe(discovery_text, pairs, state, filters):
    found = DISCOVERY.findall(discovery_text)
    raw = exact = None

    if found:
        raw, exact, _ = found[-1]
        raw, exact = int(raw), int(exact)

    warm = sorted(set(WARM.findall(discovery_text)))
    identities = [normalize_pair(pair) for pair in pairs]
    tokens = [p.get('token') for p in identities]

    duplicates = sorted(
        t for t, count in Counter(tokens).items()
        if t and count > 1
    )

    shapes = {}
    if isinstance(state, dict):
        for name, value in state.items():
            name = str(name)

            if any(
                x in name.lower()
                for x in (
                    'secret', 'key', 'credential',
                    'rpc', 'wallet'
                )
            ):
                continue

            if isinstance(value, (list, tuple, dict, set)):
                shapes[name[:70]] = {
                    'kind': type(value).__name__,
                    'length': len(value)
                }
            elif isinstance(
                value, (bool, int, float, type(None))
            ):
                shapes[name[:70]] = {
                    'kind': type(value).__name__,
                    'value': value
                }

    return {
        'build': 'ORACLE243',
        'discovery_raw': raw,
        'discovery_exact_pairs': exact,
        'prepared_pairs': len(pairs),
        'distinct_prepared_tokens': len(set(tokens)),
        'prepared_pair_identities': identities,
        'warmed_token_prefixes': warm,
        'duplicate_prepared_tokens': duplicates,
        'discovery_minus_prepared': (
            exact - len(pairs)
            if exact is not None else None
        ),
        'state_shapes': shapes,
        'prepare_once_selection_conditions': filters,
        'bridge_certified': (
            exact is not None
            and exact == len(pairs)
            and not duplicates
        ),
        'next_gate': (
            'HOLD_UNPROVEN_ROUTE_HYDRATION'
            if exact != len(pairs)
            else 'REVIEW_PREPARED_COVERAGE'
        ),
        'signing': False,
        'broadcast': False,
        'execution_admission': False
    }


def test():
    class Pair:
        token = 'A' * 32
        pump_pool = 'B' * 32
        meteora_pool = 'C' * 32

    sample = (
        '[CROSSLIST_DISCOVERY] raw=40 '
        'exact_pairs=11 '
        'failures={"NO_DLMM_PAIR":29}\n'
        '[ORACLE025_TOKEN_WARM] token=AAAAA '
        'program=Token'
    )

    result = describe(
        sample,
        [Pair()],
        {'pairs': [Pair()], 'stage': 4},
        []
    )

    assert result['discovery_exact_pairs'] == 11
    assert result['prepared_pairs'] == 1
    assert result['discovery_minus_prepared'] == 10
    assert result['bridge_certified'] is False
    assert result['signing'] is False
    assert result['broadcast'] is False
    assert result['warmed_token_prefixes'] == ['AAAAA']

    print(
        '[ORACLE243_TEST_PASS] '
        'boundary_counts=TRUE identities=TRUE '
        'no_execution=TRUE'
    )


def run():
    if os.getenv(
        'QSB_LIVE_ARM', 'NO'
    ).upper() != 'NO':
        raise RuntimeError('HOLD_LIVE_ARM')

    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_IN_CHILD')

    if not os.getenv(
        'SOLANA_RPC_URL', ''
    ).startswith('https://'):
        raise RuntimeError('HOLD_RPC_NOT_CONFIGURED')

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as guard

    original = r.q87.c.rpc
    log = io.StringIO()
    state = {}
    pairs = []
    error = None

    filters = source_filters(r.q25.prepare_once)

    try:
        r.q87.c.rpc = guard.restricted_rpc_factory(
            original
        )

        with contextlib.redirect_stdout(log):
            state, _ = r.q25.prepare_once(Path.cwd())
            r.q25.bind_cached_state(state)
            r.install_proven_hot_math(state)
            pairs = list(state.get('pairs') or [])

    except Exception as exc:
        error = type(exc).__name__

    finally:
        r.q87.c.rpc = original

    result = describe(
        log.getvalue(), pairs, state, filters
    )
    result['preparation_error_type'] = error
    result['bridge_certified'] = (
        result['bridge_certified']
        and error is None
    )

    OUT.parent.mkdir(
        parents=True, exist_ok=True
    )
    OUT.write_text(
        json.dumps(result, indent=2),
        encoding='utf-8'
    )

    print(
        '[ORACLE243_BOUNDARY]',
        json.dumps({
            'raw': result['discovery_raw'],
            'exact_pairs': result[
                'discovery_exact_pairs'
            ],
            'hydrated': result['prepared_pairs'],
            'gap': result[
                'discovery_minus_prepared'
            ],
            'warm_tokens': result[
                'warmed_token_prefixes'
            ],
            'error': error,
            'execution': False
        }, sort_keys=True)
    )

    for row in result['prepared_pair_identities']:
        print(
            '[ORACLE243_PREPARED]',
            json.dumps({
                'token': row.get('token', '')[:12],
                'pump': row.get(
                    'pump_pool', ''
                )[:12],
                'meteora': row.get(
                    'meteora_pool', ''
                )[:12],
                'fields': sorted(row)
            }, sort_keys=True)
        )

    print(
        '[ORACLE243_STATE_SHAPES]',
        json.dumps(
            result['state_shapes'],
            sort_keys=True
        )
    )

    print(
        '[ORACLE243_FILTER_COUNT]',
        len(filters)
    )

    print(
        '[ORACLE243_RESULT]',
        result['next_gate']
    )
    print('[REPORT]', OUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test', action='store_true'
    )
    parser.add_argument(
        '--run', action='store_true'
    )
    args = parser.parse_args()

    if not (args.test or args.run):
        parser.error(
            'specify --test or --run'
        )

    if args.test:
        test()

    if args.run:
        run()