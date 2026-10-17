
"""ORACLE193 full installer: reverse-specific Meteora Swap2 account binding."""
import argparse, ast
from pathlib import Path
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST=ROOT/'oracle193_reverse_direction_aware_swap2.py'
CODE=r'''"""Simulation-only reverse Swap2 ATA direction binding; scanner unchanged."""
import argparse,copy,os,subprocess,sys
from . import runtime as r
from . import oracle192_swap2_idl_truth as q192

def expected_reverse(template,user):
    fixed=list(template.get('fixed_accounts') or [])
    if len(fixed)!=15:raise RuntimeError('ORACLE193_BAD_FIXED_LAYOUT')
    x,y=str(template.get('token_x')),str(template.get('token_y'))
    wsol=str(r.q87.c.WSOL)
    if (x==wsol)==(y==wsol):raise RuntimeError('ORACLE193_PAIR_NOT_WSOL')
    prog_x,prog_y=str(fixed[11][0]),str(fixed[12][0])
    if x==wsol:
        incoming=r.q87.c.ata(user,x,prog_x)
        outgoing=r.q87.c.ata(user,y,prog_y)
    else:
        incoming=r.q87.c.ata(user,y,prog_y)
        outgoing=r.q87.c.ata(user,x,prog_x)
    revised=copy.deepcopy(fixed)
    revised[4]=(incoming,False,True)
    revised[5]=(outgoing,False,True)
    return revised

def certify(route,direction):
    if direction!='METEORA_TO_PUMP':
        return q192_original(route,direction)
    token=str(route.get('token',''))
    template=r.METEORA_TEMPLATES.get(token)
    if not isinstance(template,dict):raise RuntimeError('ORACLE193_TEMPLATE_MISSING')
    user=str(r.USER or '')
    if not user:raise RuntimeError('ORACLE193_USER_NOT_READY')
    expected=expected_reverse(template,user)
    ix=route.get('meteora_ix') or {}
    metas=ix.get('accounts') or []
    actual=[str(m.get('pubkey')) for m in metas[:16]]
    keys=[str(x[0]) for x in expected]
    keys.insert(13,q192.MEMO)
    drift=[i for i,(a,b) in enumerate(zip(actual,keys)) if a!=b]
    if len(actual)!=16 or drift:
        print('[ORACLE193_REVERSE_ACCOUNT_DRIFT] index_only=%s broadcast=FALSE'%drift,flush=True)
        raise RuntimeError('ORACLE193_REVERSE_BINDING_MISMATCH')
    # Only adapt validation expectations; do not change on-chain instructions.
    original_fixed=template['fixed_accounts']
    template['fixed_accounts']=expected
    try:
        validated=q192_original(route,direction)
    finally:
        template['fixed_accounts']=original_fixed
    print('[ORACLE193_REVERSE_BINDING_PASS] wsol_in=TRUE token_out=TRUE broadcast=FALSE',flush=True)
    return validated

q192_original=q192.certify

def worker():
    if os.getenv('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ORACLE193_ARMED_REFUSED')
    armed=getattr(r,'_live_010_armed',None)
    if not callable(armed) or armed():
        raise RuntimeError('ORACLE193_DISARM_NOT_CERTIFIED')
    q192.certify=certify
    try:q192.worker()
    finally:q192.certify=q192_original

def run():
    import build_oracle_182_secure_windows_credentials as vault
    db=vault.api();h=vault.load(db,vault.HELIUS);s=vault.load(db,vault.SOLANA)
    if not h or not s:raise RuntimeError('ORACLE193_VAULT_MISSING')
    env=os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY']=s
    env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['QSB_LIVE_ARM']='NO'
    return subprocess.call([sys.executable,'-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.oracle193_reverse_direction_aware_swap2',
        '--worker'],env=env)

def test():
    ws=str(r.q87.c.WSOL)
    token='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
    user=str(r.q87.c.MRIYA_WALLET)
    f=[('PLACEHOLDER',False,False) for _ in range(15)]
    f[11]=(str(r.q87.c.TOKEN),False,False)
    f[12]=(str(r.q87.c.TOKEN22),False,False)
    t={'token_x':ws,'token_y':token,'fixed_accounts':f}
    e=expected_reverse(t,user)
    assert e[4][0]==r.q87.c.ata(user,ws,str(r.q87.c.TOKEN))
    assert e[5][0]==r.q87.c.ata(user,token,str(r.q87.c.TOKEN22))
    t['token_x'],t['token_y']=t['token_y'],t['token_x']
    t['fixed_accounts'][11],t['fixed_accounts'][12]=t['fixed_accounts'][12],t['fixed_accounts'][11]
    e=expected_reverse(t,user)
    assert e[4][0]==r.q87.c.ata(user,ws,str(r.q87.c.TOKEN))
    assert e[5][0]==r.q87.c.ata(user,token,str(r.q87.c.TOKEN22))
    print('[TEST PASS] ORACLE193 WSOL-in/token-out both mint positions',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--run',action='store_true')
    g.add_argument('--worker',action='store_true');a=p.parse_args()
    test() if a.test else sys.exit(run()) if a.run else worker()
'''
def test():
    ast.parse(CODE)
    assert 'q192.worker()' in CODE and "env['QSB_LIVE_ARM']='NO'" in CODE
    print('[INSTALLER TEST PASS] ORACLE193 parses; simulation only')
def install():
    for dep in ('runtime.py','oracle192_swap2_idl_truth.py'):
        if not (ROOT/dep).is_file():raise RuntimeError('ORACLE193_MISSING_'+dep)
    if DEST.exists() and DEST.read_text(encoding='utf-8')!=CODE:
        raise RuntimeError('ORACLE193_DESTINATION_DIFFERS')
    DEST.write_text(CODE,encoding='utf-8');ast.parse(CODE)
    print('[INSTALL PASS] ORACLE193 reverse WSOL binding; scanner unchanged')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');a=p.parse_args()
    test() if a.test else install()
