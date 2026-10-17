"""ORACLE-266: fail-closed SDK termination and historical partial classification."""
import argparse
import ast
import inspect
import json
import textwrap
from collections import Counter
from pathlib import Path

BASE = Path('runtime_state/oracle/oracle_live_execution')
RAW = BASE / 'ORACLE258_ROTATION_RAW.json'
OUT = BASE / 'ORACLE266_SDK_TERMINATION_GATE.json'
SIZES = tuple(10_000_000 + 5_000_000*i for i in range(19))


def quote_contract(source):
    tree = ast.parse(textwrap.dedent(source))
    fn = next((x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'quote'), None)
    if fn is None:
        raise ValueError('QUOTE_FUNCTION_NOT_FOUND')
    snippets = []
    for node in ast.walk(fn):
        if isinstance(node, (ast.Return, ast.Raise)):
            e = ast.unparse(node.value if isinstance(node, ast.Return) else node.exc)
            if any(w in e for w in ('Quote(', 'InsufficientBinArrays')):
                snippets.append({'line': node.lineno, 'kind': type(node).__name__, 'expression': e[:300]})
    return sorted(snippets, key=lambda x:x['line'])


def classify(data):
    if data.get('build') != 'ORACLE241' or any(data.get(k) is not False for k in ('signing','broadcast','execution_admission')):
        raise ValueError('UNTRUSTED_INPUT')
    rows = data.get('observations')
    if not isinstance(rows,list):
        raise ValueError('OBSERVATIONS_MISSING')
    counts, by_token = Counter(), {}
    for row in rows:
        if not isinstance(row,dict) or row.get('exception_code') != 'DLMM_PARTIAL':
            continue
        size, mint = row.get('size_sol'), row.get('mint')
        if type(size) not in (float,int) or not isinstance(mint,str):
            counts['INVALID_ROW'] += 1
            continue
        start = round(size * 1_000_000_000)
        if start not in SIZES:
            counts['INVALID_SIZE'] += 1
            continue
        counts['FAILED_OBSERVATIONS'] += 1
        key = mint[:12]
        bucket = by_token.setdefault(key,Counter())
        calls = row.get('dlmm_calls')
        if not isinstance(calls,list):
            counts['CALLS_UNAVAILABLE'] += 1
            continue
        for call in calls:
            if not isinstance(call,dict) or type(call.get('remaining_in')) is not int:
                counts['REMAINING_UNAVAILABLE'] += 1
                continue
            rem = call['remaining_in']
            category = 'ZERO_REMAINING' if rem==0 else 'MATCHES_SOL_INPUT' if rem==start else 'OTHER_POSITIVE' if rem>0 else 'NEGATIVE_INVALID'
            counts[category]+=1
            bucket[category]+=1
            if call.get('complete') is True and rem>0:
                counts['COMPLETE_TRUE_NONZERO_REMAINING']+=1
    return counts,by_token


def test():
    sample='''def quote(pool, amount_in, swap_for_y, strict=True):
    if not pool: raise InsufficientBinArrays(0, amount_in, None)
    if amount_in: return Quote(0, 1, complete=True, remaining_in=amount_in)
    return Quote(0,1)
'''
    paths=quote_contract(sample)
    assert len(paths)==3 and any(x['kind']=='Raise' for x in paths)
    data={'build':'ORACLE241','signing':False,'broadcast':False,'execution_admission':False,'observations':[
        {'mint':'A'*32,'size_sol':.01,'exception_code':'DLMM_PARTIAL','dlmm_calls':[{'complete':True,'remaining_in':10000000}]}]}
    counts,_=classify(data)
    assert counts['MATCHES_SOL_INPUT']==1 and counts['COMPLETE_TRUE_NONZERO_REMAINING']==1
    data['broadcast']=True
    try:classify(data)
    except ValueError:pass
    else:raise AssertionError('UNSAFE_INPUT_ACCEPTED')
    print('[ORACLE266_TEST_PASS] sdk_paths=TRUE partial_evidence=TRUE fail_closed=TRUE')


def run():
    import meteora_dlmm
    fn=meteora_dlmm.quote
    paths=quote_contract(inspect.getsource(fn))
    counts,by_token=classify(json.loads(RAW.read_text(encoding='utf-8')))
    result={'build':'ORACLE266','sdk_quote_module':getattr(fn,'__module__','UNKNOWN'),
            'sdk_termination_paths':paths,'partial_counts':dict(counts),
            'by_token':{k:dict(v) for k,v in sorted(by_token.items())},
            'sdk_partial_means_liquidity_exhaustion_certified':False,
            'bin_arrays_complete_certified':False,'freshness_certified':False,
            'execution_admission':False,'signing':False,'broadcast':False,
            'status':'HOLD_BIN_COVERAGE_AND_FULL_FILL'}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE266_RESULT]',json.dumps({k:v for k,v in result.items() if k not in ('sdk_termination_paths','by_token')},sort_keys=True))
    for path in paths:print('[ORACLE266_SDK_PATH]',json.dumps(path,sort_keys=True))
    for key,value in result['by_token'].items():print('[ORACLE266_TOKEN]',json.dumps({'token':key,**value},sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()
