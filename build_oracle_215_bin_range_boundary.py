"""ORACLE215: offline DLMM bin-range and zero-fill decision boundary."""
import argparse
import ast
import inspect
import json
import textwrap
from pathlib import Path

STATE = Path('runtime_state/oracle/oracle_live_execution')
SOURCE = STATE / 'ORACLE213_DLMM_PARTIAL_EVIDENCE.json'
OUT = STATE / 'ORACLE215_BIN_RANGE_BOUNDARY.json'


def source(fn):
    result = textwrap.dedent(inspect.getsource(fn))
    ast.parse(result)
    return result


def excerpt(fn, terms, radius=5):
    lines = source(fn).splitlines()
    keep = set()
    for i, line in enumerate(lines):
        if any(term in line.lower() for term in terms):
            keep.update(range(max(0, i-radius), min(len(lines), i+radius+1)))
    return [{'line': i+1, 'text': lines[i]} for i in sorted(keep)]


def summarize(data):
    calls = data.get('captured_dlmm_calls') or []
    zero = [r for r in calls if r.get('complete') is False and
            isinstance(r.get('requested_raw'), int) and
            r['requested_raw'] > 0 and r.get('remaining_raw') == r['requested_raw']]
    tokens = sorted({r.get('token', '') for r in zero})
    return {'total_calls': len(calls), 'zero_fill_count': len(zero),
            'zero_fill_tokens': tokens, 'cause': 'NOT_YET_DETERMINED'}


def test():
    def fixture(n):
        if n > 0:
            return n
        raise RuntimeError('NO_BIN')
    assert excerpt(fixture, ['raise', 'return'])
    result = summarize({'captured_dlmm_calls': [
        {'token': 'A', 'complete': False, 'requested_raw': 25,
         'remaining_raw': 25}]})
    assert result['zero_fill_count'] == 1
    assert result['cause'] == 'NOT_YET_DETERMINED'
    print('[ORACLE215_TEST_PASS] boundary_extraction=TRUE zero_fill_accounting=TRUE')


def run():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle199_opportunity_freeze as freeze)
    from meteora_dlmm import PoolState, quote
    freeze.freeze()
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    if data.get('build') != 'ORACLE213' or data.get('broadcast') is not False:
        raise RuntimeError('ORACLE215_SOURCE_INVALID')

    targets = {
        'quote': (quote, ('loaded_', 'missing_bin', 'pool.bins',
                          'mm_reserve', 'open_amt', 'proc_amt', 'strict')),
        'from_accounts': (PoolState.from_accounts,
                          ('array', 'bin', 'active', 'account', 'return')),
        'loaded_bin_range': (PoolState.loaded_bin_range,
                             ('bin', 'array', 'return', 'raise')),
    }
    sections = {}
    for name, (fn, terms) in targets.items():
        sections[name] = {'file': Path(inspect.getfile(fn)).name,
                          'function': getattr(fn, '__qualname__', name),
                          'excerpt': excerpt(fn, terms)}
        print('[ORACLE215_SOURCE]', name, sections[name]['file'])
        for item in sections[name]['excerpt']:
            print('%s:%04d %s' % (name, item['line'], item['text']))

    report = {'build': 'ORACLE215', 'status': 'OFFLINE_RESEARCH_ONLY',
              'zero_fill': summarize(data), 'sections': sections,
              'missing_bin_arrays_confirmed': False,
              'insufficient_pool_liquidity_confirmed': False,
              'rpc': False, 'signing': False, 'broadcast': False}
    STATE.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE215_ZERO_FILL]', report['zero_fill'])
    print('[REPORT]', OUT)
    freeze.freeze()
    print('[ORACLE215_PASS] freeze=PASS rpc=FALSE signing=FALSE broadcast=FALSE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test', action='store_true')
    group.add_argument('--run', action='store_true')
    args = parser.parse_args()
    test() if args.test else run()
