"""ORACLE-275: fail-closed account dependency manifest; offline, zero RPC."""
import argparse
import ast
import json
import os
import time
from collections import Counter
from pathlib import Path

import build_oracle_269_persistent_token_lifecycle as life
import build_oracle_270_verified_pool_ws_lifecycle as bridge
import build_oracle_272_ws_account_state_capture as capture
import build_oracle_273_canonical_ws_hydration_gate as gate

BASE = Path('runtime_state/oracle/oracle_live_execution')
OUT = BASE / 'ORACLE275_REQUIRED_ACCOUNT_MANIFEST.json'
CORE = Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
FUNCTIONS = ('build_token_snapshot','dlmm_arrays','dlmm_quote_snapshot')
GRID = [round(.010+.005*i,3) for i in range(19)]


def source_contract(path):
    tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    result={}
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name not in FUNCTIONS:
            continue
        calls=[];fields=[]
        for child in ast.walk(node):
            if isinstance(child,ast.Call):
                calls.append(ast.unparse(child.func)[:100])
            if isinstance(child,ast.Subscript) and isinstance(child.slice,ast.Constant) and isinstance(child.slice.value,str):
                fields.append(child.slice.value)
        result[node.name]={'source_line':node.lineno,'called_functions':sorted(set(calls)),
                           'referenced_fields':sorted(set(fields))}
    if set(result)!=set(FUNCTIONS):raise RuntimeError('CANONICAL_HYDRATOR_CONTRACT_CHANGED')
    return result


def manifest(state,inventory,now,contract,max_age=120):
    inspected=gate.evaluate(state,inventory,now,max_age=max_age)
    rows=[];verified=Counter()
    for token in sorted({mint for refs in inventory.values() for mint,_ in refs}):
        venues={}
        for address,refs in inventory.items():
            for mint,venue in refs:
                if mint!=token:continue
                data=state['accounts'].get(address)
                status=gate.check_account(address,data,inventory,now,max_age) if data else 'NOT_CAPTURED'
                venues.setdefault(venue,[]).append({'address':address,'status':status,
                          'slot':data.get('slot') if status=='VALID_CAPTURED_BYTES' else None})
                verified[status]+=1
        ready_p=any(x['status']=='VALID_CAPTURED_BYTES' for x in venues.get('PUMPSWAP_WS',[]))
        ready_m=any(x['status']=='VALID_CAPTURED_BYTES' for x in venues.get('METEORA_WS',[]))
        rows.append({'token':token,'pool_accounts':venues,
            'fresh_pump_pool':ready_p,'fresh_meteora_pool':ready_m,
            'missing_required_account_classes':['PUMP_BASE_VAULT','PUMP_QUOTE_VAULT',
                'METEORA_BIN_ARRAYS','METEORA_VAULTS_OR_TOKEN_LAYOUT_VALIDATION'],
            'missing_account_addresses_unresolved':True,
            'safe_to_reprice':False})
    return {'build':'ORACLE275','status':'HOLD_REQUIRED_ACCOUNT_ADDRESS_RESOLUTION',
      'token_count':len(rows),'pool_account_checks':dict(verified),
      'fresh_two_venue_pool_pairs':inspected['verified_pair_candidates'],
      'required_account_classes':['PUMP_BASE_VAULT','PUMP_QUOTE_VAULT',
                'METEORA_BIN_ARRAYS','METEORA_VAULTS_OR_TOKEN_LAYOUT_VALIDATION'],
      'canonical_function_contract':contract,'tokens':rows,'size_grid':GRID,
      'rpc_poll_calls':0,'canonical_full_hydration':False,
      'local_pricing_connected':False,'fee_adjusted_net_certified':False,
      'execution_admission':False,'signing':False,'broadcast':False}


def test():
    import base64,hashlib,tempfile
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'core.py'
        path.write_text('def build_token_snapshot(x):\n return x["pump_pool"]\n'
            'def dlmm_arrays(x):\n return list(x)\n'
            'def dlmm_quote_snapshot(x):\n return x["dlmm_state"]\n',encoding='utf-8')
        contract=source_contract(path)
    token='A'*32;a='B'*32;b='C'*32;owner='D'*32;now=10000.0
    inv={a:[(token,'PUMPSWAP_WS')],b:[(token,'METEORA_WS')]}
    state=capture.empty()
    for addr,venue,slot in [(a,'PUMPSWAP_WS',100),(b,'METEORA_WS',101)]:
        raw=addr.encode();state['accounts'][addr]={'address':addr,'slot':slot,'owner':owner,
           'received_epoch':now,'data_b64':base64.b64encode(raw).decode(),
           'fingerprint':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw),'refs':[[token,venue]]}
    r=manifest(state,inv,now,contract)
    assert r['fresh_two_venue_pool_pairs']==1 and r['token_count']==1
    assert not r['tokens'][0]['safe_to_reprice'] and r['rpc_poll_calls']==0
    assert manifest(state,inv,now+121,contract)['fresh_two_venue_pool_pairs']==0
    state['signing']=True
    try:manifest(state,inv,now,contract)
    except RuntimeError:pass
    else:raise AssertionError('UNTRUSTED_CAPTURE_ACCEPTED')
    print('[ORACLE275_TEST_PASS] source_contract=TRUE live_pool_evidence=TRUE stale_hold=TRUE no_rpc=TRUE no_orders=TRUE')


def run():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    if not CORE.is_file():raise RuntimeError('CANONICAL_CORE_MISSING')
    db=life.load(life.DB)
    inventory=bridge.inventory(bridge.INPUTS,set(db['tokens']))
    if not inventory:raise RuntimeError('CANONICAL_INVENTORY_MISSING')
    output=manifest(capture.load(capture.STATE),inventory,time.time(),source_contract(CORE))
    BASE.mkdir(parents=True,exist_ok=True)
    capture.save(OUT,output)
    print('[ORACLE275_RESULT]',json.dumps({k:v for k,v in output.items() if k not in ('tokens','canonical_function_contract')},sort_keys=True))
    for k,v in output['canonical_function_contract'].items():
        print('[ORACLE275_DEPENDENCY]',json.dumps({'function':k,**v},sort_keys=True))
    for r in output['tokens'][:16]:
        print('[ORACLE275_TOKEN]',json.dumps({'token':r['token'][:12],
             'pump_fresh':r['fresh_pump_pool'],'meteora_fresh':r['fresh_meteora_pool'],
             'ready':False},sort_keys=True))
    print('[REPORT]',OUT)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not (a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()