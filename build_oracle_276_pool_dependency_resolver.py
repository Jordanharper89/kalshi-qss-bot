"""ORACLE-276: resolve known Pump vault addresses from saved pool bytes; zero RPC."""
import argparse
import ast
import base64
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

import build_oracle_269_persistent_token_lifecycle as life
import build_oracle_270_verified_pool_ws_lifecycle as bridge
import build_oracle_272_ws_account_state_capture as capture

BASE = Path('runtime_state/oracle/oracle_live_execution')
OUT = BASE / 'ORACLE276_RESOLVED_DEPENDENCIES.json'
CORE = Path('qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py')
GRID = [round(.010 + .005 * i, 3) for i in range(19)]


def decoder_contract(path):
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    names = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    match = [n for n in names if n.name == 'decode_pump_pool']
    if len(match) != 1:
        raise RuntimeError('PUMP_DECODER_CONTRACT_UNAVAILABLE')
    node = match[0]
    if len(node.args.posonlyargs) + len(node.args.args) != 1:
        raise RuntimeError('PUMP_DECODER_SIGNATURE_CHANGED')
    return {'function':node.name, 'line':node.lineno, 'single_raw_argument':True}


def verified_bytes(entry):
    if not isinstance(entry, dict) or not isinstance(entry.get('data_b64'), str):
        raise ValueError('MISSING_ACCOUNT_BYTES')
    try:
        raw = base64.b64decode(entry['data_b64'], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError('INVALID_ACCOUNT_BYTES') from exc
    if not 0 < len(raw) <= capture.MAX_BYTES or hashlib.sha256(raw).hexdigest() != entry.get('fingerprint') or len(raw) != entry.get('byte_count'):
        raise ValueError('CAPTURE_INTEGRITY_FAILURE')
    if not bridge.valid_address(entry.get('owner')) or type(entry.get('slot')) is not int or entry['slot'] <= 0:
        raise ValueError('CAPTURE_IDENTITY_FAILURE')
    return raw


def resolve(state, inventory, decode):
    if (state.get('build') != 'ORACLE272' or state.get('schema') != 1 or
        any(state.get(x) is not False for x in ('signing','broadcast','execution_admission'))):
        raise RuntimeError('UNTRUSTED_CAPTURE')
    records = []; statuses = Counter(); needed = set()
    for address, refs in sorted(inventory.items()):
        for mint, venue in refs:
            if venue != 'PUMPSWAP_WS':
                continue
            item = {'token':mint, 'pump_pool':address, 'pump_base_vault':None,
                    'pump_quote_vault':None, 'meteora_bin_arrays_resolved':False,
                    'vault_account_bytes_verified':False, 'safe_to_reprice':False}
            entry = state.get('accounts', {}).get(address)
            try:
                if not entry:raise ValueError('POOL_CAPTURE_MISSING')
                raw = verified_bytes(entry)
                if address != entry.get('address') or [mint,venue] not in entry.get('refs',[]):
                    raise ValueError('POOL_REFERENCE_MISMATCH')
                decoded = decode(raw)
                if not isinstance(decoded, dict):raise ValueError('UNEXPECTED_PUMP_DECODER_RESULT')
                base, quote = decoded.get('base_vault'), decoded.get('quote_vault')
                if not bridge.valid_address(base) or not bridge.valid_address(quote) or base == quote:
                    raise ValueError('PUMP_VAULT_ADDRESS_NOT_RESOLVED')
                item.update(pump_base_vault=base,pump_quote_vault=quote,
                            status='PUMP_VAULT_ADDRESSES_RESOLVED_UNVERIFIED')
                needed.update((base,quote))
            except (ValueError, KeyError, TypeError, IndexError, RuntimeError, AssertionError) as exc:
                item['status'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
                if len(item['status']) > 70:item['status'] = item['status'][:70]
            statuses[item['status']] += 1
            records.append(item)
    return {'build':'ORACLE276','status':'HOLD_VAULT_BIN_BYTES_AND_OWNER_PROGRAMS',
        'pump_pairs_inspected':len(records),'resolution_statuses':dict(statuses),
        'unique_pump_vault_addresses':sorted(needed), 'pump_vault_count':len(needed),
        'tokens':records,'unresolved_account_classes':['METEORA_BIN_ARRAYS','METEORA_VAULTS',
          'PUMP_VAULT_ACCOUNT_BYTES','OWNER_PROGRAM_AND_TOKEN_MINT_VALIDATION'],
        'saved_capture_is_current':False,'full_hydration':False,'size_grid':GRID,
        'rpc_poll_calls':0,'local_pricing_connected':False,'execution_admission':False,
        'signing':False,'broadcast':False}


def test():
    addr='B'*32; token='A'*32; owner='C'*32; base='D'*32; quote='E'*32; raw=b'fixture'
    state=capture.empty();state['accounts'][addr]={'address':addr,'owner':owner,'slot':10,
        'fingerprint':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw),
        'data_b64':base64.b64encode(raw).decode(),'refs':[[token,'PUMPSWAP_WS']]}
    r=resolve(state,{addr:[(token,'PUMPSWAP_WS')]},lambda b:{'base_vault':base,'quote_vault':quote})
    assert r['pump_vault_count']==2 and len(r['size_grid'])==19
    assert not r['tokens'][0]['safe_to_reprice'] and r['rpc_poll_calls']==0
    state['accounts'][addr]['fingerprint']='0'*64
    assert resolve(state,{addr:[(token,'PUMPSWAP_WS')]},lambda b: {})['pump_vault_count']==0
    state['signing']=True
    try:resolve(state,{},lambda b:{})
    except RuntimeError:pass
    else:raise AssertionError('UNSAFE_CAPTURE_ACCEPTED')
    print('[ORACLE276_TEST_PASS] vault_decode=TRUE hash=TRUE fail_closed=TRUE sizes=19 no_rpc=TRUE')


def run():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_CHILD_REQUIRED')
    decoder_contract(CORE)
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    db=life.load(life.DB)
    inv=bridge.inventory(bridge.INPUTS,set(db['tokens']))
    if not inv:raise RuntimeError('CANONICAL_INVENTORY_MISSING')
    result=resolve(capture.load(capture.STATE),inv,core.decode_pump_pool)
    capture.save(OUT,result)
    print('[ORACLE276_RESULT]',json.dumps({k:v for k,v in result.items() if k not in ('tokens','unique_pump_vault_addresses','size_grid')},sort_keys=True))
    for row in result['tokens']:
        print('[ORACLE276_TOKEN]',json.dumps({**row,'token':row['token'][:12]},sort_keys=True))
    print('[REPORT]',OUT)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if not(a.test or a.run):p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()
