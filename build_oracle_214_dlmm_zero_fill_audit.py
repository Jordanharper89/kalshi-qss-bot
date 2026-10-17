"""ORACLE214 offline DLMM zero-fill pipeline audit; frozen executor untouched."""
import argparse
import ast
import hashlib
import inspect
import json
import textwrap
from pathlib import Path

STATE = Path('runtime_state/oracle/oracle_live_execution')
OUT = STATE / 'ORACLE214_DLMM_ZERO_FILL_AUDIT.json'
SOURCE = STATE / 'ORACLE213_DLMM_PARTIAL_EVIDENCE.json'
TERMS = ('bin', 'array', 'liquid', 'reserve', 'active', 'amount', 'remaining',
         'complete', 'swap_for', 'return', 'raise', 'decode', 'index')


def outline(fn):
    src = textwrap.dedent(inspect.getsource(fn))
    ast.parse(src)
    lines = src.splitlines()
    matches = [{'line': i, 'code': line.rstrip()}
               for i, line in enumerate(lines, 1)
               if any(t in line.lower() for t in TERMS)]
    return {'name': fn.__module__ + '.' + fn.__name__,
            'file': Path(inspect.getfile(fn)).name,
            'sha256': hashlib.sha256(src.encode('utf-8')).hexdigest(),
            'source_lines': len(lines), 'selected_lines': matches}


def interpret(report):
    calls = report.get('captured_dlmm_calls', [])
    partials = [x for x in calls if x.get('complete') is False
                or x.get('remaining_raw') not in (None, 0)]
    zero = [x for x in partials if isinstance(x.get('requested_raw'), int)
            and x['requested_raw'] > 0
            and x.get('remaining_raw') == x['requested_raw']]
    return {'dlmm_calls': len(calls), 'partial_calls': len(partials),
            'zero_fill_calls': len(zero),
            'zero_fill_tokens': sorted(set(x.get('token', '') for x in zero)),
            'all_partials_zero_fill': len(partials) > 0 and len(zero) == len(partials)}


def test():
    def sample(amount):
        if amount < 0:
            raise ValueError('negative')
        return amount
    assert outline(sample)['selected_lines']
    result = interpret({'captured_dlmm_calls': [
        {'requested_raw': 100, 'remaining_raw': 100, 'complete': False, 'token': 'T'}]})
    assert result['zero_fill_calls'] == 1 and result['all_partials_zero_fill']
    print('[ORACLE214_TEST_PASS] offline_source_and_zero_fill_accounting')


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze, runtime as r)
    import meteora_dlmm
    freeze.freeze()
    report = json.loads(SOURCE.read_text(encoding='utf-8'))
    if report.get('build') != 'ORACLE213' or report.get('broadcast') is not False:
        raise RuntimeError('ORACLE214_SOURCE_GUARD')
    q60b2 = r.q25.prepare_once.__globals__['q60b2']
    q60b = q60b2.prepare_once.__globals__['q60b']
    original = q60b.extended_prepare.__globals__['_ORIG_PREPARE']
    pd = original.__globals__['pd']
    functions = {'build_dlmm_state': pd._build_dlmm_state,
                 'load_dlmm_arrays': pd.c.dlmm_arrays,
                 'strict_dlmm_quote': meteora_dlmm.quote}
    inspected = {}
    for name, fn in functions.items():
        inspected[name] = outline(fn)
        print('[ORACLE214_SOURCE]', name, inspected[name]['file'],
              'lines='+str(inspected[name]['source_lines']))
        for row in inspected[name]['selected_lines']:
            print('%s:%04d %s' % (name, row['line'], row['code']))
    result = {'build': 'ORACLE214', 'status': 'OFFLINE_SOURCE_AUDIT',
              'evidence': interpret(report), 'functions': inspected,
              'zero_fill_cause_confirmed': False,
              'wallet_loaded': False, 'signing': False, 'broadcast': False}
    STATE.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE214_ZERO_FILL]', result['evidence'])
    print('[REPORT]', OUT)
    freeze.freeze()
    print('[ORACLE214_PASS] executor_unchanged=TRUE rpc=FALSE broadcast=FALSE')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test', action='store_true')
    g.add_argument('--run', action='store_true')
    a = p.parse_args()
    test() if a.test else run()
