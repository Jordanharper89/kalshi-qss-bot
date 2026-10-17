
"""ORACLE191 installer: isolated official Swap2 account order test."""
import argparse,ast
from pathlib import Path
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST=ROOT/'oracle191_swap2_official_order.py'
CODE=r'''"""Test official Meteora Swap2 accounts, simulation only; no runtime modifications."""
import argparse,copy,os,sys,subprocess
from . import runtime as r
from . import oracle190_reverse_preload_balance as q190
from . import oracle181_direct_swap2_certification as q181

DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MEMO='MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
PUMP='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
ORDER=(0,8,1,2,3,4,5,6,7,9,10,11,12,15,14,13)

def correct(route,direction):
    template=r.METEORA_TEMPLATES.get(str(route.get('token')))
    if not isinstance(template,dict):
        raise RuntimeError('ORACLE191_NO_WARM_TEMPLATE')
    original=route.get('meteora_ix')
    if not isinstance(original,dict) or original.get('programId')!=DLMM:
        raise RuntimeError('ORACLE191_NO_DLMM_SWAP')
    accounts=copy.deepcopy(original.get('accounts') or [])
    fixed=template.get('fixed_accounts') or []
    if len(fixed)!=15 or len(accounts)<17:
        raise RuntimeError('ORACLE191_UNEXPECTED_ACCOUNT_COUNT')
    def key(i):
        return str(accounts[i].get('pubkey',''))
    if not (key(0)==template['pool'] and key(9)==DLMM
            and key(13)==MEMO and key(14)==str(fixed[13][0])
            and key(15)==DLMM):
        raise RuntimeError('ORACLE191_ORACLE180_LAYOUT_DRIFT')

    ordered=[copy.deepcopy(accounts[i]) for i in ORDER]
    if not (ordered[1]['pubkey']==str(fixed[8][0])
            and ordered[13]['pubkey']==DLMM
            and ordered[14]['pubkey']==str(fixed[13][0])
            and ordered[15]['pubkey']==MEMO):
        raise RuntimeError('ORACLE191_OFFICIAL_ORDER_MISMATCH')

    # Anchor optional host_fee_in=None uses the DLMM program sentinel.
    ordered[9]['isWritable']=False
    ordered[13]['isWritable']=False
    tail=accounts[16:]
    allowed={str(x[1]) for x in template['arrays']}
    if not tail or any(x.get('pubkey') not in allowed or
                       x.get('isWritable') is not True for x in tail):
        raise RuntimeError('ORACLE191_BIN_ARRAY_NOT_WARM')
    revised=copy.deepcopy(original)
    revised['accounts']=ordered+tail
    out=dict(route)
    out['meteora_ix']=revised

    candidates=[]
    for name,ixs in route.get('original_candidates') or []:
        positions=[i for i,x in enumerate(ixs)
                   if x.get('programId')==DLMM]
        if len(positions)!=1:
            raise RuntimeError('ORACLE191_DLMM_LEG_COUNT')
        pos=positions[0]
        if ixs[pos].get('data')!=original.get('data'):
            raise RuntimeError('ORACLE191_DATA_MISMATCH')
        new=copy.deepcopy(ixs)
        new[pos]=copy.deepcopy(revised)
        if not any(x.get('programId')==PUMP for x in new):
            raise RuntimeError('ORACLE191_PUMP_LEG_MISSING')
        candidates.append((name,new))
    if not candidates:
        raise RuntimeError('ORACLE191_NO_CANDIDATES')
    out['original_candidates']=candidates
    print('[ORACLE191_SWAP2_OFFICIAL] direction=%s named=16 bins=%d order=VERIFIED broadcast=FALSE' %
          (direction,len(tail)),flush=True)
    return out

def run():
    if os.getenv('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ORACLE191_ARMED_REFUSED')
    old=r._fast_010_profit_lock_route

    def guarded(route,direction,bound):
        result=old(route,direction,bound)
        if not isinstance(result,tuple) or len(result)!=3:
            raise RuntimeError('ORACLE191_LOCK_CONTRACT_CHANGED')
        return correct(result[0],direction),result[1],result[2]

    previous_inspect=q181.inspect_route
    def inspect_official(route):
        ix=route.get('meteora_ix') or {}
        a=ix.get('accounts') or []
        if len(a)<17 or a[13].get('pubkey')!=DLMM or a[15].get('pubkey')!=MEMO:
            raise RuntimeError('ORACLE191_OFFICIAL_LAYOUT_NOT_PRESENT')
        return {'candidate_count':len(route.get('original_candidates') or []),
                'swap2_bin_arrays':len(a)-16}

    r._fast_010_profit_lock_route=guarded
    q181.inspect_route=inspect_official
    try:
        q190.worker()
    finally:
        r._fast_010_profit_lock_route=old
        q181.inspect_route=previous_inspect

def test():
    import base64
    fixed=[('X'+str(i),False,False) for i in range(15)]
    fixed[0]=('pool',False,True)
    fixed[9]=(DLMM,False,True)
    fixed[13]=('event',False,False)
    fixed[14]=(DLMM,False,False)
    a=[{'pubkey':x[0],'isSigner':x[1],'isWritable':x[2]} for x in fixed]
    a.insert(13,{'pubkey':MEMO,'isSigner':False,'isWritable':False})
    a.append({'pubkey':'bin','isSigner':False,'isWritable':True})
    ix={'programId':DLMM,'accounts':a,
        'data':base64.b64encode(bytes([65,75,63,76,235,91,91,136])+bytes(17)).decode()}
    pump={'programId':PUMP}
    old=r.METEORA_TEMPLATES.copy()
    try:
        r.METEORA_TEMPLATES['T']={
            'pool':'pool','fixed_accounts':fixed,'arrays':[(1,'bin')]}
        out=correct({'token':'T','meteora_ix':ix,
                     'original_candidates':[('native',[ix,pump])]},
                    'METEORA_TO_PUMP')
        got=out['meteora_ix']['accounts']
        assert [got[i]['pubkey'] for i in (1,9,13,14,15)]==[
            'X8',DLMM,DLMM,'event',MEMO]
        assert out['original_candidates'][0][1][0]['accounts']==got
    finally:
        r.METEORA_TEMPLATES.clear()
        r.METEORA_TEMPLATES.update(old)
    print('[TEST PASS] ORACLE191 official 16 named accounts + verified bin arrays; disarmed')

def launch():
    import build_oracle_182_secure_windows_credentials as vault
    db=vault.api()
    h=vault.load(db,vault.HELIUS)
    s=vault.load(db,vault.SOLANA)
    if not h or not s:
        raise RuntimeError('ORACLE191_VAULT_MISSING')
    env=os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY']=s
    env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['QSB_LIVE_ARM']='NO'
    return subprocess.call([sys.executable,'-m',
      'qseries_v2.oracle_execution.solana_atomic_executor.oracle191_swap2_official_order',
      '--worker'],env=env)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true')
    g.add_argument('--run',action='store_true')
    g.add_argument('--worker',action='store_true')
    x=p.parse_args()
    test() if x.test else sys.exit(launch()) if x.run else run()
'''

def test():
    ast.parse(CODE)
    assert 'q190.worker()' in CODE
    assert 'ORACLE191_ARMED_REFUSED' in CODE
    print('[INSTALLER TEST PASS] ORACLE191 standalone account order source parsed')

def install():
    for f in ('runtime.py','oracle190_reverse_preload_balance.py'):
        if not (ROOT/f).is_file():
            raise RuntimeError('ORACLE191_DEPENDENCY_MISSING_'+f)
    if DEST.exists() and DEST.read_text(encoding='utf-8')!=CODE:
        raise RuntimeError('ORACLE191_EXISTING_MODULE_DIFFERS')
    DEST.write_text(CODE,encoding='utf-8')
    ast.parse(DEST.read_text(encoding='utf-8'))
    print('[INSTALL PASS] ORACLE191 standalone official Swap2 order; scanner untouched')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    a=p.parse_args()
    test() if a.test else install()
