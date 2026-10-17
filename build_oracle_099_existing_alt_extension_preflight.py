"""ORACLE-099 full installer: verify existing ALT and prepare extension admission report."""
import argparse, ast
from pathlib import Path
TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_099_existing_alt_extension_preflight.py')
SOURCE=r'''"""Read-only mainnet ALT extension admission. No keys, signing, or broadcasting."""
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
'''

def test():
    ast.parse(SOURCE)
    scope={'__name__':'oracle099_test'}
    import sys,types
    alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    class Pubkey:
        def __init__(self,b):self.b=bytes(b)
        @classmethod
        def from_string(cls,s):
            n=0
            for c in s:n=n*58+alphabet.index(c)
            b=(b'\0'*(len(s)-len(s.lstrip('1'))))+n.to_bytes((n.bit_length()+7)//8,'big')
            assert len(b)==32
            return cls(b)
        @classmethod
        def from_bytes(cls,b):return cls(b)
        def __bytes__(self):return self.b
        def __str__(self):
            n=int.from_bytes(self.b,'big');out=''
            while n:n,d=divmod(n,58);out=alphabet[d]+out
            return '1'*(len(self.b)-len(self.b.lstrip(b'\0')))+out
    fake=types.ModuleType('solders.pubkey');fake.Pubkey=Pubkey
    pkg=types.ModuleType('solders');pkg.pubkey=fake
    sys.modules['solders']=pkg;sys.modules['solders.pubkey']=fake
    exec(compile(SOURCE,'<oracle099>','exec'),scope)
    authority='DshvULBw4foHgiqLksn8H6vHWredDT6mrJBmKLTFJih6'
    addresses=['8FZiH18SPftb88k8on81jzEQbGBAyztaAKYqT7KH5CAx','So11111111111111111111111111111111111111112','ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw']
    want=addresses+['4BEMesYzs2Gucu5m5nQKgoze7pawLYHTWPzReThAdXS6','FQTs7tHw8vM9tUCU6PuRB3r6VK835cvMWZBJBHiBXKoq','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb','2tqyiusynfmwfgFDndWR2FszsCrwMJ4r7GJP9BAXGJxE','7jehcf8mPFTwwvKVtMZJBjtN3xPf5tiu625GWwGnAKYG']
    raw=bytearray(56)
    raw[:4]=bytes([1,0,0,0]);raw[4:12]=((1<<64)-1).to_bytes(8,'little');raw[21]=1;raw[22:54]=bytes(Pubkey.from_string(authority))
    raw+=b''.join(bytes(Pubkey.from_string(x)) for x in addresses)
    plan={'public_payer':authority,'selected_addresses':want}
    result=scope['inspect'](bytes(raw),scope['ALT_PROGRAM'],plan,'table')
    assert result['covered_count']==3 and result['missing_count']==5 and not result['broadcast']
    for broken in [bytes(raw[:4]+b'\0'*4+raw[8:]),bytes(raw[:21]+b'\0'+raw[22:])]:
        try:scope['inspect'](broken,scope['ALT_PROGRAM'],plan,'table')
        except RuntimeError:pass
        else:raise AssertionError('INVALID_ALT_ACCEPTED')
    print('[PASS] ORACLE099_DETERMINISTIC_ALT_AUTHORITY_COVERAGE_TESTS')
    print('[BOUNDARY] TEST_NO_RPC_NO_KEYS_NO_SIGNING_NO_BROADCAST')

def install():
    test()
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    if TARGET.exists() and TARGET.read_text(encoding='utf-8')!=SOURCE:
        raise RuntimeError('EXISTING_ORACLE099_DIFFERS_REFUSE_OVERWRITE')
    TARGET.write_text(SOURCE,encoding='utf-8')
    print('[PASS] ORACLE099_EXISTING_ALT_EXTENSION_PREFLIGHT_INSTALLED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--test',action='store_true');args=parser.parse_args()
    test() if args.test else install()
