from __future__ import annotations
import argparse,base64,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
ALT_PROGRAM='AddressLookupTab1e1111111111111111111111111'
REGISTRY=Path('runtime_state/oracle/solana_atomic_executor/canonical_alt.json')
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_151_CANONICAL_ALT_LIVE_PROOF.json')
EXPLICIT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_149_ALT_KEYS.json')
MAX_SLOT=(1<<64)-1

def canonical_address():
    row=json.loads(REGISTRY.read_text(encoding='utf-8'))
    addr=row.get('address') if isinstance(row,dict) else None
    if not isinstance(addr,str) or len(q87.c.b58d(addr))!=32:
        raise RuntimeError('CANONICAL_ALT_ADDRESS_INVALID')
    return addr

def decode_account(raw):
    if len(raw)<56 or (len(raw)-56)%32:
        return {'ok':False,'reason':'ALT_ACCOUNT_DATA_LENGTH_INVALID'}
    # Solana ALT: u32 state, u64 deactivation_slot, then remaining metadata.
    # Deactivation starts at byte 4, not byte 0.
    state=int.from_bytes(raw[0:4],'little')
    if state!=1:
        return {'ok':False,'reason':'ALT_STATE_NOT_LOOKUP_TABLE','state':state}
    deactivation=int.from_bytes(raw[4:12],'little')
    entries=(len(raw)-56)//32
    if deactivation!=MAX_SLOT:
        return {'ok':False,'reason':'ALT_DEACTIVATION_SCHEDULED',
                'deactivation_slot':deactivation,'entries':entries}
    if entries==0:
        return {'ok':False,'reason':'ALT_EMPTY'}
    return {'ok':True,'entries':entries,'active':True,
            'deactivation_slot':'MAX_U64'}

def probe(rpc=None):
    addr=canonical_address()
    rpc=rpc or q87.c.rpc
    response=rpc('getAccountInfo',[addr,{'encoding':'base64',
                                         'commitment':'confirmed'}])
    account=(response or {}).get('value')
    if not isinstance(account,dict):
        return {'ok':False,'reason':'ALT_ACCOUNT_NOT_FOUND','address':addr}
    if account.get('owner')!=ALT_PROGRAM:
        return {'ok':False,'reason':'ALT_PROGRAM_OWNER_MISMATCH',
                'address':addr}
    data=account.get('data')
    if not isinstance(data,list) or not data or not isinstance(data[0],str):
        return {'ok':False,'reason':'ALT_ACCOUNT_DATA_MISSING',
                'address':addr}
    result=decode_account(base64.b64decode(data[0],validate=True))
    return {'address':addr,**result}

def verify():
    try:
        result=probe()
    except Exception as exc:
        result={'ok':False,'reason':'ALT_RPC_OR_REGISTRY_ERROR',
                'error_class':type(exc).__name__}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    if result['ok']:
        EXPLICIT.parent.mkdir(parents=True,exist_ok=True)
        EXPLICIT.write_text(
            json.dumps({'alt_keys':[result['address']]},indent=2),
            encoding='utf-8')
        print('[ORACLE151_CANONICAL_ALT_VERIFIED] entries=%d active=TRUE owner=ALT_PROGRAM'
              %result['entries'])
        print('[ORACLE151_ALT_BOUND] canonical public ALT configured')
    else:
        if EXPLICIT.exists():
            EXPLICIT.unlink()
        print('[ORACLE151_HOLD] reason='+result['reason'])
    print('[REPORT]',REPORT)
    print('[GUARD] no signing; no broadcasting; scanner unchanged')
    return 0 if result['ok'] else 2

def test():
    from tempfile import TemporaryDirectory
    from unittest.mock import patch
    mk=lambda slot,n=1,state=1:(
        state.to_bytes(4,'little')+
        slot.to_bytes(8,'little')+
        bytes(44)+bytes([11])*32*n)
    assert decode_account(mk(MAX_SLOT))['ok']
    assert decode_account(mk(MAX_SLOT))['entries']==1
    assert decode_account(mk(123))['reason']=='ALT_DEACTIVATION_SCHEDULED'
    assert decode_account(mk(MAX_SLOT,n=0))['reason']=='ALT_EMPTY'
    assert decode_account(mk(MAX_SLOT,state=0))['reason']=='ALT_STATE_NOT_LOOKUP_TABLE'
    with TemporaryDirectory() as folder:
        p=Path(folder)/'canonical_alt.json'
        p.write_text(json.dumps({
            'address':'HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'}))
        good=lambda m,a:{'value':{
            'owner':ALT_PROGRAM,
            'data':[base64.b64encode(mk(MAX_SLOT)).decode(),'base64']}}
        with patch(__name__+'.REGISTRY',p):
            assert probe(good)['ok']
            bad=lambda m,a:{'value':{
                'owner':'11111111111111111111111111111111',
                'data':[base64.b64encode(mk(MAX_SLOT)).decode(),'base64']}}
            assert probe(bad)['reason']=='ALT_PROGRAM_OWNER_MISMATCH'
    print('[TEST PASS] ORACLE152 ALT metadata offset and safety guards')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.test:
        test()
    elif a.verify:
        raise SystemExit(verify())
    else:
        p.error('Use --test or --verify')

if __name__=='__main__':
    main()
