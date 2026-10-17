"""ORACLE-246: read-only atomic-pair preparation call-chain audit."""
import argparse
import ast
import contextlib
import inspect
import io
import json
import os
import re
import textwrap
from pathlib import Path

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE246_ATOMIC_HYDRATION_LINEAGE.json')
DISCOVERY = re.compile(r'\[CROSSLIST_DISCOVERY\] raw=(\d+) exact_pairs=(\d+)')


def describe_function(fn, depth=0):
    try:
        lines, first = inspect.getsourcelines(fn)
        module = inspect.getmodule(fn)
        tree = ast.parse(textwrap.dedent(''.join(lines)))
    except (OSError, TypeError, SyntaxError):
        return {'name': getattr(fn, '__name__', '?'), 'source_available': False}
    conditions, calls, assignments = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While)):
            conditions.append({
                'line': first + node.lineno - 1,
                'condition': ast.unparse(node.test)[:220]
            })
        if isinstance(node, ast.Call):
            calls.append(ast.unparse(node.func)[:120])
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            s = ast.unparse(node)[:190]
            if any(k in s.lower() for k in (
                'pairs', 'hydrate', 'crosslist', 'warm', 'candidate'
            )):
                assignments.append({
                    'line': first + node.lineno - 1,
                    'expression': s
                })
    return {
        'name': fn.__name__,
        'module': getattr(module, '__name__', '?'),
        'file': Path(inspect.getsourcefile(fn) or '?').name,
        'line': first,
        'conditions': conditions[:35],
        'calls': list(dict.fromkeys(calls))[:50],
        'assignments': assignments[:30]
    }


def resolve_calls(fn, detail):
    """Follow referenced Python functions without invoking them."""
    found = []
    namespace = getattr(fn, '__globals__', {})
    for call in detail.get('calls', []):
        parts = call.split('.')
        if not 1 <= len(parts) <= 3:
            continue
        if not all(p.isidentifier() for p in parts):
            continue
        obj = namespace.get(parts[0])
        if obj is None:
            continue
        try:
            for part in parts[1:]:
                obj = inspect.getattr_static(obj, part)
        except (AttributeError, TypeError):
            continue
        if inspect.isfunction(obj) and obj is not fn:
            module = getattr(obj, '__module__', '')
            if module.startswith('qseries_v2.'):
                found.append(obj)
    return found


def call_chain(root, max_functions=16):
    queue, visited, records = [root], set(), []
    while queue and len(records) < max_functions:
        fn = queue.pop(0)
        ident = (fn.__module__, fn.__qualname__)
        if ident in visited:
            continue
        visited.add(ident)
        info = describe_function(fn)
        records.append(info)
        queue.extend(resolve_calls(fn, info))
    return records


def classify(state, text, chain):
    discovered = DISCOVERY.findall(text)
    pairs = state.get('pairs') or []
    ids = [{
        'mint_prefix': str(getattr(p, 'token', ''))[:12],
        'pump_prefix': str(getattr(p, 'pump_pool', ''))[:12],
        'meteora_prefix': str(getattr(p, 'meteora_pool', ''))[:12]
    } for p in pairs]
    exact = int(discovered[-1][1]) if discovered else None
    return {
        'raw_discovered': int(discovered[-1][0]) if discovered else None,
        'exact_discovered': exact,
        'hydrated': len(pairs),
        'gap': exact - len(pairs) if exact is not None else None,
        'prepared': ids,
        'chain': chain,
        'chain_functions': len(chain),
        'registry_warning':
            'creg keys are not verified atomic route identities',
        'execution_admission': False,
        'signing': False,
        'broadcast': False,
        'status': 'HOLD_EXACT_HYDRATION_EXCLUSIONS_UNPROVEN'
    }


def test():
    def producer():
        pairs = []
        if not pairs:
            return pairs
        return pairs

    chain = call_chain(producer)
    assert chain
    assert any(
        'not pairs' in x['condition']
        for x in chain[0]['conditions']
    )
    result = classify(
        {'pairs': [object()]},
        '[CROSSLIST_DISCOVERY] raw=38 exact_pairs=10',
        chain
    )
    assert result['gap'] == 9
    assert result['execution_admission'] is False
    print(
        '[ORACLE246_TEST_PASS] call_chain=TRUE '
        'conditions=TRUE gap=TRUE disarmed=TRUE'
    )


def run():
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('HOLD_LIVE_ARM')
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_KEY_PRESENT')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise RuntimeError('HOLD_RPC_MISSING')

    from qseries_v2.oracle_execution.solana_atomic_executor \
        import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor \
        import oracle186_direct_route_truth as guard

    chain = call_chain(r.q25.prepare_once)
    original = r.q87.c.rpc
    state, error, capture = {}, None, io.StringIO()

    try:
        r.q87.c.rpc = guard.restricted_rpc_factory(original)
        with contextlib.redirect_stdout(capture):
            state, _ = r.q25.prepare_once(Path.cwd())
            r.q25.bind_cached_state(state)
            r.install_proven_hot_math(state)
    except Exception as exc:
        error = type(exc).__name__
    finally:
        r.q87.c.rpc = original

    result = classify(state, capture.getvalue(), chain)
    result['error'] = error
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')

    print('[ORACLE246_BOUNDARY]', json.dumps({
        k: result[k] for k in (
            'raw_discovered', 'exact_discovered',
            'hydrated', 'gap', 'chain_functions', 'error'
        )
    }, sort_keys=True))

    for item in chain:
        print('[ORACLE246_FUNCTION]', json.dumps(item, sort_keys=True))

    print(
        '[ORACLE246_RESULT]', result['status'],
        'signing=FALSE broadcast=FALSE'
    )
    print('[REPORT]', OUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if not (args.test or args.run):
        parser.error('specify --test or --run')
    if args.test:
        test()
    if args.run:
        run()