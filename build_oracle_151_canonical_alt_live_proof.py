from pathlib import Path
import ast, py_compile

DEST=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle151_canonical_alt_live_proof.py')
SOURCE=r'''from __future__ import annotations
import argparse, base64, json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87

ALT_PROGRAM='AddressLookupTab1e1111111111111111111111111'
REGISTRY=Path('runtime_state/oracle/solana_atomic_executor/canonical_alt.json')
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_151_CANONICAL_ALT_LIVE_PROOF.json')
EXPLICIT=Path('runtime_state/oracle/oracle_live_execution/ORACLE_149_ALT_KEYS.json')

def canonical_address():
    row=json.loads(REGISTRY.read_text(encoding='utf-8'))
    if not isinstance(row,dict) or not isinstance(row.get('address'),str):
        raise RuntimeError('CANONICAL_ALT_ADDRESS_MISSING')
    address=row['address']
    if len(q87.c.b58d(address))!=32:raise RuntimeError('CANONICAL_ALT_ADDRESS_INVALID')
    return address

def probe(rpc=None):
    addr=canonical_address()
    rpc=rpc or q87.c.rpc
    reply=rpc('getAccountInfo',[addr,{'encoding':'base64','commitment':'confirmed'}])
    acct=(reply or {}).get('value')
    if not isinstance(acct,dict):return {'ok':False,'address':addr,'reason':'ALT_ACCOUNT_NOT_FOUND'}
    if acct.get('owner')!=ALT_PROGRAM:
        return {'ok':False,'address':addr,'reason':'ALT_PROGRAM_OWNER_MISMATCH','owner':acct.get('owner')}
    data=acct.get('data')
    if not isinstance(data,list) or not data or not isinstance(data[0],str):
        return {'ok':False,'address':addr,'reason':'ALT_ACCOUNT_DATA_MISSING'}
    raw=base64.b64decode(data[0],validate=True)
    if len(raw)<56 or (len(raw)-56)%32:
        return {'ok':False,'address':addr,'reason':'ALT_ACCOUNT_DATA_LENGTH_INVALID','raw_length':len(raw)}
    n=(len(raw)-56)//32
    # ALT metadata contains deactivation slot in the first 8 bytes.
    deactivation=int.from_bytes(raw[:8],'little')
    if deactivation!=2**64-1:
        return {'ok':False,'address':addr,'reason':'ALT_DEACTIVATION_SCHEDULED','entries':n}
    if n==0:return {'ok':False,'address':addr,'reason':'ALT_EMPTY'}
    return {'ok':True,'address':addr,'entries':n,'owner_verified':True,'active':True}

def verify():
    try:out=probe()
    except Exception as exc:
        # Never print exception strings: RPC URLs can contain credential parameters.
        out={'ok':False,'reason':'ALT_RPC_OR_REGISTRY_ERROR','error_class':type(exc).__name__}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(out,indent=2),encoding='utf-8')
    if out['ok']:
        # Explicit discovery list is a public address only; never include ordinary pool keys.
        EXPLICIT.parent.mkdir(parents=True,exist_ok=True)
        EXPLICIT.write_text(json.dumps({'alt_keys':[out['address']]},indent=2),encoding='utf-8')
        print('[ORACLE151_CANONICAL_ALT_VERIFIED] entries=%d active=TRUE owner=ALT_PROGRAM'%out['entries'])
        print('[ORACLE151_ALT_BOUND] public canonical ALT configured for ORACLE149')
    else:print('[ORACLE151_HOLD] reason='+out['reason'])
    print('[REPORT]',REPORT)
    print('[GUARD] no signing; no broadcasting; scanner unchanged')
    return 0 if out['ok'] else 2

def test():
    from tempfile import TemporaryDirectory
    from unittest.mock import patch
    from pathlib import Path
    with TemporaryDirectory() as d:
        p=Path(d)/'canonical_alt.json';p.write_text(json.dumps({'address':'HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r'}))
        with patch(__name__+'.REGISTRY',p):
            valid=(2**64-1).to_bytes(8,'little')+bytes(48)+bytes([11])*32
            mk=lambda owner,blob:{'value':{'owner':owner,'data':[base64.b64encode(blob).decode(),'base64']}}
            ok=probe(lambda m,a:mk(ALT_PROGRAM,valid))
            assert ok['ok'] and ok['entries']==1
            assert probe(lambda m,a:mk('11111111111111111111111111111111',valid))['reason']=='ALT_PROGRAM_OWNER_MISMATCH'
            assert probe(lambda m,a:mk(ALT_PROGRAM,bytes(56)))['reason']=='ALT_DEACTIVATION_SCHEDULED'
    print('[TEST PASS] ORACLE151 owner, nonempty ALT, active/deactivation guards; no transactions')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--verify',action='store_true');a=p.parse_args()
    if a.test:test()
    elif a.verify:raise SystemExit(verify())
    else:p.error('Use --test or --verify')
if __name__=='__main__':main()
'''
def install():
    ast.parse(SOURCE)
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(SOURCE,encoding='utf-8')
    py_compile.compile(str(DEST),doraise=True)
    print('[INSTALL PASS] ORACLE151 canonical ALT live verifier installed')
    print('[SCOPE] verifies one canonical ALT, no signing/broadcast/scanner edits')
if __name__=='__main__':install()
