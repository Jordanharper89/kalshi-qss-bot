"""MTR-162 exact native instruction producer contract; source only."""
import ast, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SOURCES={
 'canonical_runtime':'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py',
 'native_core':'qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py',
 'qarb_087':'qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering/qarb_087_two_second_compaction_liquidity_repair.py',
 'atomic_preflight':'mtr_119_canonical_alt_atomic_preflight.py'}
OUT=ROOT/'runtime_state/oracle/oracle_live_execution/mtr_162_native_instruction_producer_contract.json'
MARKERS=('instruction','pump','meteora','swap','route','compile','build','native','merge','signed_tx','dlmm')
def inspect(path):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    rows=[]
    for n in ast.walk(tree):
        if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        calls=sorted(set(ast.unparse(x.func) for x in ast.walk(n) if isinstance(x,ast.Call)))
        if not any(k in n.name.lower() for k in MARKERS) and not any(
            k in x.lower() for x in calls for k in ('merge_native','pump_ix','dlmm_ix','compile_candidate','signed_tx')):continue
        rows.append({'name':n.name,'line':n.lineno,
            'args':[a.arg for a in n.args.args],
            'calls':[c for c in calls if any(k in c.lower() for k in MARKERS)][:35]})
    return sorted(rows,key=lambda x:x['line'])
def run():
    result={'mtr':'MTR-162','scope':'EXACT_NATIVE_PRODUCER_CONTRACT',
            'sources':{},'missing':[],'instructions_produced':False,
            'scanner_modified':False,'private_key_used':False,
            'signing':False,'broadcast':False}
    for label,rel in SOURCES.items():
        path=ROOT/rel
        if not path.is_file():result['missing'].append(rel);continue
        result['sources'][label]={'path':rel,'functions':inspect(path)}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    for label,row in result['sources'].items():
        print('[MTR162_SOURCE]',label,row['path'])
        for f in row['functions']:
            print('[MTR162_FN]',label,f['line'],f['name'],'args='+','.join(f['args']))
            if f['calls']:print('[MTR162_CALLS]',','.join(f['calls']))
    print('[MTR162_MISSING]',result['missing'])
    print('[REAL_INSTRUCTION_PACKAGE] NOT_YET_PRODUCED')
    print('[SCANNER] FROZEN')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
    print('[REPORT]',OUT)
    if result['missing']:raise SystemExit('[HOLD] MISSING_CANONICAL_SOURCE')
    return result
if __name__=='__main__':run()
