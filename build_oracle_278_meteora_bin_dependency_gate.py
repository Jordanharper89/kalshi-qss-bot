"""ORACLE-278: read-only Meteora bin dependency and funded RPC budget gate."""
import argparse, ast, base64, hashlib, json, os, time
from collections import Counter
from pathlib import Path
import build_oracle_269_persistent_token_lifecycle as life
import build_oracle_270_verified_pool_ws_lifecycle as bridge

BASE=Path('runtime_state/oracle/oracle_live_execution')
CORE=Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
POOL=BASE/'ORACLE272_WS_ACCOUNT_STATES.json'
VAULT=BASE/'ORACLE277_ACCOUNT_BYTES.json'
OUT=BASE/'ORACLE278_METEORA_BIN_DEPENDENCY_GATE.json'
GRID=[round(.010+.005*i,3) for i in range(19)]

def contract(path):
    tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    targets={}
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name not in ('dlmm_arrays','build_token_snapshot','dlmm_quote_snapshot'):continue
        calls=[]
        for n in ast.walk(node):
            if isinstance(n,ast.Call):
                callee=ast.unparse(n.func)
                if callee in ('rpc','account','dlmm_arrays','PoolState.from_accounts','quote'):
                    calls.append({'line':n.lineno,'callee':callee,'arguments':[ast.unparse(a)[:130] for a in n.args[:2]]})
        targets[node.name]={'line':node.lineno,'calls':calls}
    if set(targets)!={'dlmm_arrays','build_token_snapshot','dlmm_quote_snapshot'}:raise RuntimeError('CANONICAL_CONTRACT_CHANGED')
    if not any(c['callee']=='rpc' for c in targets['dlmm_arrays']['calls']):raise RuntimeError('DLMM_ARRAY_RPC_BOUNDARY_NOT_FOUND')
    return targets

def load(path,expected):
    if not path.is_file():return {}
    d=json.loads(path.read_text(encoding='utf-8'))
    if d.get('build')!=expected or any(d.get(k) is not False for k in ('signing','broadcast','execution_admission')):raise RuntimeError('UNTRUSTED_CAPTURE_'+expected)
    if not isinstance(d.get('accounts'),dict):raise RuntimeError('INVALID_ACCOUNTS_'+expected)
    return d['accounts']

def check(entry,address):
    if not isinstance(entry,dict) or entry.get('address')!=address:return 'NO_BYTES'
    encoded=entry.get('data_b64')
    try:raw=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError):return 'CORRUPT_BYTES'
    if not raw or hashlib.sha256(raw).hexdigest()!=entry.get('fingerprint') or len(raw)!=entry.get('byte_count'):return 'CORRUPT_BYTES'
    if not bridge.valid_address(entry.get('owner')):return 'OWNER_INVALID'
    return 'CAPTURE_VALID_HISTORICAL'

def produce(inv,pool,vault,code):
    rows=[]; counts=Counter(); seen=set()
    for addr,refs in sorted(inv.items()):
        for mint,venue in refs:
            if venue!='METEORA_WS' or (addr,mint) in seen:continue
            seen.add((addr,mint))
            pool_status=check(pool.get(addr),addr)
            if pool_status=='NO_BYTES':pool_status=check(vault.get(addr),addr)
            counts[pool_status]+=1
            rows.append({'token':mint,'meteora_pool':addr,'pool_capture':pool_status,
                'program_owner_observed':(pool.get(addr) or vault.get(addr) or {}).get('owner') if pool_status=='CAPTURE_VALID_HISTORICAL' else None,
                'bin_array_addresses':[], 'bin_arrays_certified':False,
                'requires_exact_pool_scoped_discovery':True,'safe_to_reprice':False})
    return {'build':'ORACLE278','token_pools':len(rows),'capture_statuses':dict(counts),
        'canonical_contract':code,'meteora_targets':rows,'rpc_budget':{'initial_discovery_calls':0,'runtime_rest_calls':0,'planned_max_initial_calls_per_run':2,'rate_limit_strategy':'NO_CALLS_UNTIL_EXACT_POOL_SCOPED_QUERY_VERIFIED'},
        'unresolved':['DLMM_POOL_SCOPED_BIN_ARRAY_ADDRESS_RESOLUTION','BIN_ARRAY_BYTES','METEORA_VAULT_OWNER_AND_MINT','FRESH_TWO_VENUE_CANONICAL_HYDRATION'],
        'size_grid':GRID,'scanner_changed':False,'local_pricing_connected':False,'execution_admission':False,
        'net_profit_certified':False,'signing':False,'broadcast':False,'status':'HOLD_EXACT_BIN_ARRAY_QUERY_CONTRACT'}

def test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'c.py';p.write_text('def dlmm_arrays(pool):\n return rpc("getProgramAccounts",[pool])\n'
            'def build_token_snapshot(pool):\n return PoolState.from_accounts(account(pool),dlmm_arrays(pool))\n'
            'def dlmm_quote_snapshot(snap):\n return quote(snap)\n',encoding='utf-8')
        co=contract(p)
    a='A'*32;m='B'*32
    result=produce({a:[(m,'METEORA_WS')]},{},{},co)
    assert result['token_pools']==1 and not result['meteora_targets'][0]['safe_to_reprice']
    assert result['rpc_budget']['runtime_rest_calls']==0 and len(result['size_grid'])==19
    assert check({'address':a,'data_b64':base64.b64encode(b'x').decode(),'fingerprint':'0'*64,'byte_count':1,'owner':m},a)=='CORRUPT_BYTES'
    print('[ORACLE278_TEST_PASS] canonical_rpc_boundary=TRUE 19_sizes=TRUE integrity=TRUE no_orders=TRUE')

def run():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('DISARMED_CHILD_REQUIRED')
    code=contract(CORE); db=life.load(life.DB)
    inv=bridge.inventory(bridge.INPUTS,set(db['tokens']))
    report=produce(inv,load(POOL,'ORACLE272'),load(VAULT,'ORACLE277'),code)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('[ORACLE278_RESULT]',json.dumps({k:v for k,v in report.items() if k not in ('meteora_targets','canonical_contract','size_grid')},sort_keys=True))
    for name,data in code.items():print('[ORACLE278_CONTRACT]',json.dumps({'function':name,**data},sort_keys=True))
    for item in report['meteora_targets']:print('[ORACLE278_TARGET]',json.dumps({**item,'token':item['token'][:12]},sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()