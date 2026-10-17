"""ORACLE267: offline DLMM quote and snapshot hydration source trace."""
import argparse
import ast
import inspect
import json
import re
from pathlib import Path

OUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE267_DLMM_HYDRATION_TRACE.json')
CORE=Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
O18=Path('qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py')
TERMS=('dlmm_state','bin_array','bin_arrays','hydrate','immutable_snapshot','meteora','InsufficientBinArrays','remaining','reserve','liquidity','active_id')
SENSITIVE=re.compile(r'private.?key|api.?key|authorization|secret|rpc_url|helius',re.I)

def inspect_source(source, file, names=None):
    tree=ast.parse(source)
    lines=source.splitlines()
    out=[]
    for fn in ast.walk(tree):
        if not isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)) or names is not None and fn.name not in names:
            continue
        hits=[i for i in range(fn.lineno,fn.end_lineno+1) if any(t in lines[i-1].lower() for t in TERMS)]
        if not hits:continue
        # Preserve surrounding context without dumping unrelated source or secrets.
        windows=sorted({i for hit in hits for i in range(max(hit-2,fn.lineno),min(hit+2,fn.end_lineno)+1)})
        snippets=[]
        for i in windows[:85]:
            code=lines[i-1].strip()[:190]
            snippets.append({'line':i,'code':'[REDACTED]' if SENSITIVE.search(code) else code})
        out.append({'file':file,'function':fn.name,'line':fn.lineno,'term_hits':len(hits),'snippets':snippets})
    return out

def collect(paths, sdk_source):
    results=[]
    for p in paths:
        if not p.is_file():raise RuntimeError('MISSING_SOURCE_'+p.name)
        results.extend(inspect_source(p.read_text(encoding='utf-8'),str(p)))
    results.extend(inspect_source(sdk_source,'INSTALLED:meteora_dlmm.quote',{'quote'}))
    # Focus on exact DLMM state origins, no arbitrary project-wide code scan.
    ordered=sorted(results,key=lambda x:(0 if x['function'] in ('dlmm_quote_snapshot','immutable_snapshot','exact_snapshot_opportunities','quote') else 1,-x['term_hits']))
    return {'build':'ORACLE267','source_functions_found':len(results),'priority_contracts':ordered[:16],
            'sdk_quote_accounting_changed':False,'scanner_changed':False,
            'hydration_coverage_certified':False,'live_pool_state_certified':False,
            'full_fill_certified':False,'net_profit_certified':False,
            'signing':False,'broadcast':False,'execution_admission':False,
            'status':'HOLD_HYDRATION_AND_BIN_COVERAGE_UNVERIFIED'}

def test():
    sample='''def quote(pool, amount_in):\n    remaining=amount_in\n    if not pool.bin_arrays:\n        raise InsufficientBinArrays(0,remaining,None)\n    return remaining\n'''
    r=inspect_source(sample,'fixture',{'quote'})
    assert len(r)==1 and r[0]['term_hits']>=2
    assert any('bin_arrays' in x['code'] for x in r[0]['snippets'])
    assert not any(SENSITIVE.search(x['code']) for x in r[0]['snippets'])
    print('[ORACLE267_TEST_PASS] targeted_source=TRUE sdk=TRUE no_rpc=TRUE disarmed=TRUE')

def run():
    import meteora_dlmm
    sdk_source=inspect.getsource(meteora_dlmm.quote)
    result=collect((CORE,O18),sdk_source)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE267_RESULT]',json.dumps({k:v for k,v in result.items() if k!='priority_contracts'},sort_keys=True))
    for item in result['priority_contracts']:
        print('[ORACLE267_CONTRACT]',json.dumps(item,sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not (a.test or a.run):p.error('choose --test or --run')
    if a.test:test()
    if a.run:run()
