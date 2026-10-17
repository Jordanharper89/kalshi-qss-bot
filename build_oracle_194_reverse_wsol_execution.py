
"""ORACLE194 single isolated reverse WSOL execution test installer."""
import argparse, ast
from pathlib import Path
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST=ROOT/'oracle194_reverse_wsol_execution.py'
CODE=r'''"""Attach real WSOL funding + SyncNative to reverse atomic candidates; simulation only."""
import argparse,base64,copy,os,struct,subprocess,sys
from . import runtime as r
from . import oracle190_reverse_preload_balance as q190
SYS='11111111111111111111111111111111'
WSOL='So11111111111111111111111111111111111111112'
DLMM='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
AMOUNT=50_000_000

def ix(program,accounts,data):
    return {'programId':program,'accounts':[{'pubkey':k,'isSigner':s,'isWritable':w} for k,s,w in accounts],
            'data':base64.b64encode(data).decode()}

def inject(route,direction):
    if direction!='METEORA_TO_PUMP':return route
    owner=getattr(r,'USER',None)
    token=str(route.get('token',''))
    template=r.METEORA_TEMPLATES.get(token)
    swap=route.get('meteora_ix') or {}
    if not owner or not isinstance(template,dict) or swap.get('programId')!=DLMM:
        raise RuntimeError('ORACLE194_CONTEXT_HOLD')
    metas=swap.get('accounts') or []
    if len(metas)<17 or str(route.get('start_lamports'))!=str(AMOUNT):
        raise RuntimeError('ORACLE194_SWAP_STRUCTURE_HOLD')
    x,y=template['token_x'],template['token_y']
    if WSOL not in (x,y) or x==y:raise RuntimeError('ORACLE194_NOT_WSOL_PAIR')
    program_x=str(template['fixed_accounts'][11][0]);program_y=str(template['fixed_accounts'][12][0])
    wsol_program=program_x if x==WSOL else program_y
    destination=str(r.q87.c.ata(owner,WSOL,wsol_program))
    source=str(metas[4].get('pubkey'))
    if source!=destination:raise RuntimeError('ORACLE194_SOURCE_NOT_WSOL_ATA')
    tr=ix(SYS,[(owner,True,True),(destination,False,True)],struct.pack('<IQ',2,AMOUNT))
    sync=ix(wsol_program,[(destination,False,True)],bytes([17]))
    original=route.get('original_candidates') or []
    updated=[]
    for row in original:
        if not isinstance(row,(tuple,list)) or len(row)!=2:raise RuntimeError('ORACLE194_BAD_CANDIDATE')
        name,ixs=row
        positions=[j for j,item in enumerate(ixs) if item.get('programId')==DLMM]
        if len(positions)!=1:raise RuntimeError('ORACLE194_DLMM_COUNT')
        j=positions[0]; seq=copy.deepcopy(ixs)
        # Source ATA creation, when present, must precede funding.
        seq[j:j]=[copy.deepcopy(tr),copy.deepcopy(sync)]
        updated.append((name,seq))
    if not updated:raise RuntimeError('ORACLE194_NO_CANDIDATES')
    out=dict(route);out['original_candidates']=updated
    print('[ORACLE194_WSOL_FUNDING_BOUND] direction=METEORA_TO_PUMP lamports=50000000 source=DERIVED_ATA candidates=%d broadcast=FALSE'%len(updated),flush=True)
    return out

def worker():
    if os.getenv('QSB_LIVE_ARM','').upper()=='YES':raise RuntimeError('ORACLE194_ARMED_REFUSED')
    armed=getattr(r,'_live_010_armed',None)
    if not callable(armed) or armed():raise RuntimeError('ORACLE194_DISARM_UNCERTIFIED')
    old=r._fast_010_profit_lock_route
    def wrapped(*args,**kwargs):
        result=old(*args,**kwargs)
        if not isinstance(result,tuple) or len(result)!=3:raise RuntimeError('ORACLE194_LOCK_CONTRACT')
        direction=args[1] if len(args)>1 else kwargs.get('direction')
        return inject(result[0],direction),result[1],result[2]
    r._fast_010_profit_lock_route=wrapped
    try:q190.worker()
    finally:r._fast_010_profit_lock_route=old

def launch():
    import build_oracle_182_secure_windows_credentials as vault
    d=vault.api();h=vault.load(d,vault.HELIUS);s=vault.load(d,vault.SOLANA)
    if not h or not s:raise RuntimeError('ORACLE194_STORED_CREDENTIALS_MISSING')
    env=os.environ.copy();env['QSB_SOLANA_PRIVATE_KEY']=s
    env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['QSB_LIVE_ARM']='NO'
    return subprocess.call([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.oracle194_reverse_wsol_execution','--worker'],env=env)

def test():
    tx=ix(SYS,[('wallet',True,True),('wsol',False,True)],struct.pack('<IQ',2,AMOUNT))
    assert base64.b64decode(tx['data'])==struct.pack('<IQ',2,AMOUNT)
    assert base64.b64decode(ix('token',[('wsol',False,True)],bytes([17]))['data'])==bytes([17])
    assert len(tx['accounts'])==2 and tx['accounts'][0]['isSigner']
    print('[TEST PASS] ORACLE194 native SOL transfer and SyncNative encodings; broadcast=FALSE')

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--worker',action='store_true')
    a=p.parse_args();test() if a.test else sys.exit(launch()) if a.run else worker()
'''
def test():
    ast.parse(CODE)
    assert 'q190.worker()' in CODE and 'QSB_LIVE_ARM' in CODE
    assert 'sendTransaction' not in CODE
    print('[INSTALLER TEST PASS] ORACLE194 parses and does not submit transactions')
def install():
    for dep in ('runtime.py','oracle190_reverse_preload_balance.py'):
        if not (ROOT/dep).is_file():raise RuntimeError('ORACLE194_MISSING_'+dep)
    if DEST.exists() and DEST.read_text(encoding='utf-8')!=CODE:
        raise RuntimeError('ORACLE194_EXISTING_MODULE_DIFFERS')
    DEST.write_text(CODE,encoding='utf-8');ast.parse(DEST.read_text(encoding='utf-8'))
    print('[INSTALL PASS] ORACLE194 isolated reverse WSOL funding; production untouched')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');a=p.parse_args()
    test() if a.test else install()
