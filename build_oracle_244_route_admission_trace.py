"""ORACLE-244: read-only exact-route admission trace; no execution."""
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
    'ORACLE244_ROUTE_ADMISSION_TRACE.json'
)
FIELDS = (
    'token', 'mint', 'base_mint', 'token_mint',
    'pump_pool', 'meteora_pool', 'pool',
    'pool_address', 'token_x', 'token_y',
    'address', 'pubkey', 'status', 'reason'
)
SENSITIVE = (
    'secret', 'private', 'credential',
    'password', 'rpc_url', 'api_key'
)
BASE58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')


def safe_value(value):
    if isinstance(value, (str, int, float, bool, type(None))):
        s = str(value)
        if isinstance(value, str) and len(s) > 100:
            return '[LONG_VALUE_REDACTED]'
        return value
    return '[%s]' % type(value).__name__


def public_fields(value):
    found = {}
    for name in FIELDS:
        try:
            item = (
                value.get(name) if isinstance(value, dict)
                else getattr(value, name, None)
            )
        except Exception:
            continue
        if item is not None:
            found[name] = safe_value(item)
    return found


def summarize(value):
    if isinstance(value, dict):
        return {
            'type': 'dict',
            'length': len(value),
            'field_names': sorted(
                str(k) for k in value
                if isinstance(k, str)
                and len(k) < 60
                and not any(
                    s in k.lower() for s in SENSITIVE
                )
            )[:25],
            'route_fields': public_fields(value)
        }

    if isinstance(value, (tuple, list)):
        return {
            'type': type(value).__name__,
            'length': len(value),
            'elements': [
                safe_value(v) for v in value[:4]
            ]
        }

    return {
        'type': type(value).__name__,
        'route_fields': public_fields(value)
    }


def registry_rows(registry):
    if not isinstance(registry, dict):
        return [], 'REGISTRY_NOT_DICT'

    rows = []
    for index, (key, value) in enumerate(registry.items()):
        if index >= 100:
            break

        row = {
            'index': index,
            'key_type': type(key).__name__,
            'key': safe_value(key),
            'value': summarize(value)
        }

        if isinstance(key, str) and BASE58.fullmatch(key):
            row['key_pubkey'] = key

        rows.append(row)

    return rows, None


def explain_source(func):
    try:
        code = inspect.getsource(func)
        path = inspect.getsourcefile(func) or ''
        node = ast.parse(code)
    except (OSError, TypeError, SyntaxError):
        return {'available': False}

    tests = []
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.While, ast.IfExp)):
            tests.append({
                'line_in_function': n.lineno,
                'condition': ast.unparse(n.test)[:180]
            })

    calls = sorted(set(
        n.func.attr for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
    ))

    return {
        'available': True,
        'module_file': Path(path).name,
        'function': func.__name__,
        'conditions': tests[:50],
        'calls': calls[:50]
    }


def make_report(state, trace, source, error=None):
    creg = (
        state.get('creg')
        if isinstance(state, dict)
        else None
    )
    rows, issue = registry_rows(creg)

    pairs = (
        list(state.get('pairs') or [])
        if isinstance(state, dict)
        else []
    )

    prepared = [public_fields(p) for p in pairs]
    prepared_tokens = {
        str(p.get('token')) for p in prepared
        if p.get('token')
    }

    for row in rows:
        fields = row['value'].get('route_fields', {})
        ids = [
            fields.get(k)
            for k in (
                'token', 'mint',
                'base_mint', 'token_mint'
            )
        ]
        ids.append(row.get('key_pubkey'))

        ids = [
            str(x) for x in ids
            if isinstance(x, str)
            and BASE58.fullmatch(x)
        ]

        hits = [
            v for v in ids
            if v in prepared_tokens
        ]

        row['identity_match'] = (
            'MATCHED_PREPARED'
            if hits
            else 'UNRESOLVED_REGISTRY_IDENTITY'
        )

        row['matched_prepared_token'] = (
            hits[0] if len(hits) == 1 else None
        )

    statuses = dict(Counter(
        r['identity_match'] for r in rows
    ))

    return {
        'build': 'ORACLE244',
        'creg_entries': len(rows),
        'hydrated_pairs': len(pairs),
        'prepared': prepared,
        'registry': rows,
        'registry_schema_issue': issue,
        'registry_match_counts': statuses,
        'prepare_source': source,
        'startup_log_markers': re.findall(
            r'^\[([A-Z0-9_]+)\]',
            trace,
            re.M
        )[:60],
        'prepare_error': error,
        'root_cause_certified': False,
        'signing': False,
        'broadcast': False,
        'execution_admission': False,
        'status': (
            'HOLD_EXACT_REJECTION_REASON_NOT_YET_CERTIFIED'
        )
    }


def test():
    class Pair:
        token = 'A' * 32
        pump_pool = 'B' * 32

    state = {
        'creg': {
            'A' * 32: {
                'token': 'A' * 32,
                'status': 'READY'
            },
            'C' * 32: {
                'token': 'C' * 32,
                'reason': 'NO_BINS'
            }
        },
        'pairs': [Pair()]
    }

    result = make_report(
        state, '', {'available': False}
    )

    assert result['creg_entries'] == 2
    assert result['hydrated_pairs'] == 1
    assert (
        result['registry_match_counts']
        ['MATCHED_PREPARED'] == 1
    )
    assert (
        result['registry_match_counts']
        ['UNRESOLVED_REGISTRY_IDENTITY'] == 1
    )
    assert result['execution_admission'] is False

    print(
        '[ORACLE244_TEST_PASS] '
        'registry_join=TRUE '
        'unresolved_preserved=TRUE '
        'disarmed=TRUE'
    )


def run():
    if os.environ.get(
        'QSB_LIVE_ARM', 'NO'
    ).upper() != 'NO':
        raise RuntimeError('HOLD_ARMED')

    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_PRESENT')

    if not os.environ.get(
        'SOLANA_RPC_URL', ''
    ).startswith('https://'):
        raise RuntimeError('HOLD_RPC_MISSING')

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as d

    state = {}
    error = None
    captured = io.StringIO()

    source = explain_source(
        r.q25.prepare_once
    )

    original = r.q87.c.rpc

    try:
        r.q87.c.rpc = (
            d.restricted_rpc_factory(original)
        )

        with contextlib.redirect_stdout(captured):
            state, _ = r.q25.prepare_once(Path.cwd())
            r.q25.bind_cached_state(state)
            r.install_proven_hot_math(state)

    except Exception as exc:
        error = type(exc).__name__

    finally:
        r.q87.c.rpc = original

    result = make_report(
        state, captured.getvalue(), source, error
    )

    OUT.parent.mkdir(
        parents=True, exist_ok=True
    )
    OUT.write_text(
        json.dumps(result, indent=2, default=str),
        encoding='utf-8'
    )

    print(
        '[ORACLE244_RESULT]',
        json.dumps({
            'creg_entries': result['creg_entries'],
            'hydrated': result['hydrated_pairs'],
            'matching': result[
                'registry_match_counts'
            ],
            'source_conditions': len(
                source.get('conditions', [])
            ),
            'error': error,
            'signing': False,
            'broadcast': False
        }, sort_keys=True)
    )

    for row in result['registry']:
        print(
            '[ORACLE244_ROUTE]',
            json.dumps({
                'index': row['index'],
                'key': row['key'],
                'identity': row['identity_match'],
                'value': row['value']
            }, sort_keys=True, default=str)
        )

    print(
        '[ORACLE244_PREPARE_SOURCE]',
        json.dumps(source, sort_keys=True)
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
        parser.error('specify --test or --run')

    if args.test:
        test()

    if args.run:
        run()