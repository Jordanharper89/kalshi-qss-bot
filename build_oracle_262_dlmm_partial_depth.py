"""ORACLE-262: offline DLMM partial-fill evidence; research only."""
import argparse
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE258_ROTATION_RAW.json'
OUT = ROOT / 'ORACLE262_DLMM_PARTIAL_DEPTH.json'
SIZES = tuple(round(.010 + i * .005, 3) for i in range(19))


def amount(v):
    if isinstance(v, bool) or not isinstance(v, (str, int, float)):
        return None
    try:
        n = Decimal(str(v))
        return n if n.is_finite() and n >= 0 else None
    except InvalidOperation:
        return None


def audit(data):
    if data.get('build') != 'ORACLE241' or any(data.get(k) is not False for k in ('signing', 'broadcast', 'execution_admission')):
        raise ValueError('UNTRUSTED_INPUT')
    if not isinstance(data.get('observations'), list):
        raise ValueError('OBSERVATIONS_MISSING')
    tokens, shapes, sizes, cycles = defaultdict(lambda: {'failures': 0, 'calls': 0, 'positive_remaining': 0, 'maximum_remaining': None, 'examples': []}), Counter(), Counter(), Counter()
    total = 0
    for row in data['observations']:
        if not isinstance(row, dict) or row.get('exception_code') != 'DLMM_PARTIAL':
            continue
        mint, size, cycle = row.get('mint'), row.get('size_sol'), row.get('cycle')
        if not isinstance(mint, str) or not 32 <= len(mint) <= 44 or type(size) not in (int, float) or not any(abs(size-s) < 1e-8 for s in SIZES):
            continue
        total += 1
        entry = tokens[mint[:12]]
        entry['failures'] += 1
        sizes[f'{size:.3f}'] += 1
        cycles[str(cycle)] += 1
        calls = row.get('dlmm_calls')
        if not isinstance(calls, list):
            shapes['MISSING_CALL_LIST'] += 1
            continue
        shapes['CALL_LENGTH_'+str(len(calls))] += 1
        for call in calls:
            entry['calls'] += 1
            if not isinstance(call, dict):
                shapes['NON_DICTIONARY_CALL'] += 1
                continue
            shapes['FIELDS_' + '_'.join(sorted(k for k in call if k in ('complete', 'remaining_in', 'direction', 'status', 'error_code', 'input_mint', 'output_mint')))] += 1
            remaining = amount(call.get('remaining_in'))
            if remaining is None:
                shapes['REMAINING_UNAVAILABLE'] += 1
                continue
            if remaining > 0:
                entry['positive_remaining'] += 1
                shapes['POSITIVE_REMAINING'] += 1
            high = entry['maximum_remaining']
            if high is None or remaining > Decimal(high):
                entry['maximum_remaining'] = str(remaining)
            if len(entry['examples']) < 3:
                entry['examples'].append({'cycle': cycle, 'size_sol': size, 'remaining_in': str(remaining),
                                          'complete': call.get('complete') if type(call.get('complete')) is bool else None,
                                          'direction': call.get('direction') if call.get('direction') in ('PUMP_TO_METEORA', 'METEORA_TO_PUMP') else None})
    output = {'build': 'ORACLE262', 'failed_quote_observations': total, 'failures_by_cycle': dict(cycles),
              'failures_by_size': dict(sorted(sizes.items())), 'call_shapes': dict(shapes),
              'affected_tokens': dict(sorted(tokens.items(), key=lambda x: -x[1]['failures'])),
              'remaining_in_units_verified': False, 'direction_from_calls_verified': False,
              'liquidity_root_cause_certified': False, 'account_freshness_certified': False,
              'net_profit_certified': False, 'execution_admission': False, 'signing': False,
              'broadcast': False, 'status': 'HOLD_PARTIAL_FILL_UNITS_AND_DIRECTION_UNVERIFIED'}
    return output


def test():
    a = 'A' * 32
    base = {'build':'ORACLE241', 'signing':False, 'broadcast':False, 'execution_admission':False,
            'observations':[{'mint':a, 'size_sol':.010, 'cycle':1, 'exception_code':'DLMM_PARTIAL',
                             'dlmm_calls':[{'complete':False, 'remaining_in':'250'}, {'complete':True, 'remaining_in':0}]}]}
    r = audit(base)
    assert r['failed_quote_observations'] == 1
    assert r['affected_tokens'][a[:12]]['positive_remaining'] == 1
    assert r['affected_tokens'][a[:12]]['maximum_remaining'] == '250'
    assert r['execution_admission'] is False
    base['signing'] = True
    try: audit(base)
    except ValueError: pass
    else: raise AssertionError('UNSAFE_SOURCE_ACCEPTED')
    print('[ORACLE262_TEST_PASS] 19_SIZES=TRUE PARTIAL_COUNTS=TRUE DISARMED=TRUE')


def run():
    if not RAW.is_file():
        raise RuntimeError('ORACLE258_RAW_MISSING')
    r = audit(json.loads(RAW.read_text(encoding='utf-8')))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2), encoding='utf-8')
    print('[ORACLE262_RESULT]', json.dumps({k:v for k,v in r.items() if k not in ('affected_tokens','failures_by_size')}, sort_keys=True))
    print('[ORACLE262_SIZE_FAILURES]', json.dumps(r['failures_by_size'], sort_keys=True))
    for name, details in r['affected_tokens'].items():
        print('[ORACLE262_TOKEN]', json.dumps({'token':name, **details}, sort_keys=True))
    print('[REPORT]', OUT)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    if not (a.test or a.run): p.error('Specify --test or --run')
    if a.test: test()
    if a.run: run()