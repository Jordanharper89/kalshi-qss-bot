"""ORACLE-260: offline quote failure and state-source investigation."""
import argparse
import ast
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
RAW = ROOT / 'ORACLE258_ROTATION_RAW.json'
OUT = ROOT / 'ORACLE260_QUOTE_ROOT_CAUSE.json'
TARGET = ('exact_snapshot_opportunities', 'immutable_snapshot', 'warm', 'run')


def shape(value):
    if isinstance(value, dict):
        return {str(k)[:65]: type(v).__name__ for k, v in value.items() if not any(s in str(k).lower() for s in ('key', 'secret', 'auth', 'url', 'endpoint', 'transaction'))}
    return type(value).__name__


def summarize(data):
    if data.get('build') != 'ORACLE241' or any(data.get(k) is not False for k in ('signing', 'broadcast', 'execution_admission')):
        raise ValueError('UNTRUSTED_RAW')
    rows = data.get('observations')
    if not isinstance(rows, list):
        raise ValueError('MISSING_OBSERVATIONS')
    failures = Counter()
    failure_fields = Counter()
    examples = defaultdict(list)
    groups = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get('status', 'UNKNOWN'))
        if status != 'FULL_FILL_GROSS_MEASURED':
            failures[status] += 1
            failure_fields.update(shape(row))
            if len(examples[status]) < 3:
                examples[status].append({'cycle': row.get('cycle'), 'size_sol': row.get('size_sol'), 'mint_prefix': str(row.get('mint', ''))[:12], 'field_types': shape(row)})
            continue
        cycle, mint, size = row.get('cycle'), row.get('mint'), row.get('size_sol')
        if type(cycle) is not int or not isinstance(mint, str) or type(size) not in (int, float):
            continue
        directions = row.get('directions', [])
        if not isinstance(directions, list):
            continue
        for q in directions:
            if not isinstance(q, dict):
                continue
            direction, gross = q.get('direction'), q.get('gross_lamports')
            if direction not in ('PUMP_TO_METEORA', 'METEORA_TO_PUMP') or type(gross) is not int:
                continue
            groups[(mint, size, direction)].append((cycle, gross))
    repeated = []
    varying = []
    for (mint, size, direction), values in groups.items():
        if len({c for c, _ in values}) < 2:
            continue
        item = {'mint_prefix':mint[:12], 'size_sol':size, 'direction':direction, 'cycle_gross':sorted(values)}
        (repeated if len({v for _, v in values}) == 1 else varying).append(item)
    return {'observations':len(rows), 'failures':dict(failures), 'failure_field_frequency':dict(failure_fields), 'failure_examples':dict(examples), 'same_quote_cross_cycle_keys':len(repeated), 'changing_quote_cross_cycle_keys':len(varying), 'repeated_examples':repeated[:8], 'changing_examples':varying[:8]}


def source_map(base):
    files = [base/'build_oracle_241_live_opportunity_sampler.py']
    files += list((base/'qseries_v2').rglob('*.py')) if (base/'qseries_v2').exists() else []
    found = []
    for path in files:
        if not path.is_file() or path.stat().st_size > 300000:
            continue
        try:
            text = path.read_text(encoding='utf-8')
            if not any(t in text for t in TARGET):
                continue
            tree = ast.parse(text)
        except (OSError, UnicodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in TARGET:
                continue
            calls = sorted({ast.unparse(n.func)[:90] for n in ast.walk(node) if isinstance(n, ast.Call)})
            raises = [n.lineno for n in ast.walk(node) if isinstance(n, ast.Raise)]
            found.append({'file':str(path), 'function':node.name, 'line':node.lineno, 'calls':calls[:35], 'raise_lines':raises[:20]})
            if len(found) >= 45:
                return found
    return found


def test():
    a = 'A'*32
    src = {'build':'ORACLE241', 'signing':False,'broadcast':False,'execution_admission':False,
           'observations':[{'mint':a,'cycle':1,'size_sol':.01,'status':'HOLD_QUOTE_RuntimeError','detail':'sensitive'},
                           {'mint':a,'cycle':1,'size_sol':.01,'status':'FULL_FILL_GROSS_MEASURED','directions':[{'direction':'PUMP_TO_METEORA','gross_lamports':-42}]},
                           {'mint':a,'cycle':2,'size_sol':.01,'status':'FULL_FILL_GROSS_MEASURED','directions':[{'direction':'PUMP_TO_METEORA','gross_lamports':-42}]}]}
    r = summarize(src)
    assert r['same_quote_cross_cycle_keys']==1 and r['failures']['HOLD_QUOTE_RuntimeError']==1
    assert 'sensitive' not in json.dumps(r)
    src['signing'] = True
    try: summarize(src)
    except ValueError: pass
    else: raise AssertionError('UNSAFE_REPORT_ACCEPTED')
    print('[ORACLE260_TEST_PASS] offline=TRUE failure_shape=TRUE repeated_quotes=TRUE secret_values_not_printed=TRUE')


def run():
    if not RAW.is_file():
        raise RuntimeError('ORACLE258_RAW_MISSING')
    data = json.loads(RAW.read_text(encoding='utf-8'))
    result = {'build':'ORACLE260','quote_audit':summarize(data),'source_map':source_map(Path.cwd()),
              'actual_exception_root_cause_certified':False, 'state_freshness_certified':False,
              'signing':False, 'broadcast':False, 'execution_admission':False,
              'status':'HOLD_EXCEPTION_DETAIL_AND_STATE_PROVENANCE'}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    q = result['quote_audit']
    print('[ORACLE260_RESULT]',json.dumps({'failures':q['failures'],'failure_field_frequency':q['failure_field_frequency'], 'same_quote_cross_cycle_keys':q['same_quote_cross_cycle_keys'], 'changing_quote_cross_cycle_keys':q['changing_quote_cross_cycle_keys'], 'source_functions':len(result['source_map']), 'status':result['status']},sort_keys=True))
    for item in result['source_map']:
        print('[ORACLE260_SOURCE]', json.dumps(item, sort_keys=True))
    for item in q['failure_examples'].get('HOLD_QUOTE_RuntimeError', []):
        print('[ORACLE260_FAILURE_SHAPE]', json.dumps(item,sort_keys=True))
    print('[REPORT]',OUT)

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--test', action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()
