"""Read-only mainnet ALT extension admission. No keys, signing, or broadcasting."""
import base64
import json
import os
import urllib.request
from pathlib import Path
from solders.pubkey import Pubkey

ROOT=Path('runtime_state/oracle/solana_atomic_executor')
ALT_PROGRAM='AddressLookupTab1e1111111111111111111111111'
MAX_ADDRESSES=256
EXPECTED_AUTHORITY='DshvULBw4foHgiqLksn8H6vHWredDT6mrJBmKLTFJih6'

def inspect(raw, owner, plan, table):
    if owner != ALT_PROGRAM or len(raw)<56 or (len(raw)-56)%32 or raw[:4]!=bytes([1,0,0,0]):
        raise RuntimeError('INVALID_MAINNET_ALT')
    if int.from_bytes(raw[4:12],'little') != (1<<64)-1:
        raise RuntimeError('ALT_NOT_ACTIVE')
    if raw[21]!=1:
        raise RuntimeError('ALT_AUTHORITY_ABSENT')
    authority=str(Pubkey.from_bytes(raw[22:54]))
    payer=plan.get('public_payer')
    if authority!=EXPECTED_AUTHORITY or payer!=authority:
        raise RuntimeError('PLAN_PAYER_NOT_ONCHAIN_AUTHORITY')
    existing=[str(Pubkey.from_bytes(raw[i:i+32])) for i in range(56,len(raw),32)]
    wanted=plan.get('selected_addresses')
    if not isinstance(wanted,list) or len(wanted)!=8 or len(set(wanted))!=8:
        raise RuntimeError('INVALID_CANONICAL_PLAN')
    if len(existing)>MAX_ADDRESSES or len(existing)+len([a for a in wanted if a not in existing])>MAX_ADDRESSES:
        raise RuntimeError('ALT_CAPACITY_EXCEEDED')
    missing=[a for a in wanted if a not in existing]
    return {'status':'READ_ONLY_EXTENSION_ADMISSION','table':table,'authority':authority,
            'existing_count':len(existing),'covered_count':len(wanted)-len(missing),
            'missing_count':len(missing),'missing_addresses':missing,
            'all_required_covered':not missing,'onchain_verified':True,
            'wallet_signer_available':False,'extension_submitted':False,
            'signing':False,'broadcast':False,'atomic_simulation_passed':False}

def rpc_account(table):
    url=os.environ.get('SOLANA_RPC_URL') or 'https://api.mainnet-beta.solana.com'
    if not url.startswith('https://'):
        raise RuntimeError('HTTPS_RPC_REQUIRED')
    body=json.dumps({'jsonrpc':'2.0','id':99,'method':'getAccountInfo',
                     'params':[table,{'encoding':'base64','commitment':'confirmed'}]}).encode()
    req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as response:
        result=json.load(response)
    if result.get('error') or not isinstance(result.get('result'),dict):
        raise RuntimeError('RPC_FAILED')
    info=result['result'].get('value')
    if not isinstance(info,dict):
        raise RuntimeError('ALT_NOT_FOUND_ONCHAIN')
    return base64.b64decode(info['data'][0],validate=True),info['owner']

def main():
    plan=json.loads((ROOT/'canonical_alt_plan.json').read_text(encoding='utf-8'))
    registry=json.loads((ROOT/'canonical_alt.json').read_text(encoding='utf-8'))
    if plan.get('revision')!='ORACLE_096_OFFLINE_CANONICAL_ALT_PLAN':
        raise RuntimeError('INVALID_PLAN_REVISION')
    table=registry.get('address')
    if not isinstance(table,str):
        raise RuntimeError('MISSING_EXISTING_ALT')
    Pubkey.from_string(table)
    raw,owner=rpc_account(table)
    report=inspect(raw,owner,plan,table)
    path=ROOT/'oracle099_existing_alt_extension_preflight.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    tmp.replace(path)
    print('[ORACLE099_MAINNET_ALT_PREFLIGHT] '+json.dumps(report,sort_keys=True))
    print('[REPORT]',path)
    print('[HOLD] NO_EXTENSION_TRANSACTION_BUILT_OR_SENT; WALLET_SIGNER_UNAVAILABLE')
    print('[BOUNDARY] READ_ONLY_NO_KEYS_NO_SIGNING_NO_BROADCAST_NO_SCANNER_CHANGE')

if __name__=='__main__':
    main()
