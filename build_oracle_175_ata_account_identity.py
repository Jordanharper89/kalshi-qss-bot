
"""ORACLE175 complete installer: verify real ATA metas on both atomic routes."""
import argparse, ast
from build_oracle_173_rpc_backoff_boundary import install_block, TARGET

MARK='# ORACLE175_ATA_ACCOUNT_IDENTITY'
BLOCK='''# ORACLE175_ATA_ACCOUNT_IDENTITY
_ORACLE175_PREVIOUS_LOCK=_fast_010_profit_lock_route

def _oracle175_pub(meta):
    return str(meta.get('pubkey','')) if isinstance(meta,dict) else ''

def _oracle175_check(route,direction):
    if not isinstance(route,dict) or not isinstance(route.get('original_candidates'),(list,tuple)):
        raise RuntimeError('ORACLE175_ROUTE_CANDIDATES_MISSING')
    token=str(route.get('token',''))
    ata='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
    pump='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
    wsol='So11111111111111111111111111111111111111112'
    meteora=route.get('meteora_ix')
    meteora_id=str(meteora.get('programId','')) if isinstance(meteora,dict) else ''
    if not token or not meteora_id or meteora_id in (ata,pump):
        raise RuntimeError('ORACLE175_MINT_OR_METEORA_MISSING')
    for _,ixs in route['original_candidates']:
        if not isinstance(ixs,(list,tuple)) or len(ixs)<4:
            raise RuntimeError('ORACLE175_ROUTE_TOO_SHORT')
        programs=[ix.get('programId') for ix in ixs if isinstance(ix,dict)]
        if len(programs)!=len(ixs) or programs[:2]!=[ata,ata]:
            raise RuntimeError('ORACLE175_ATA_PREFIX_ABSENT')
        addresses=[]
        for idx,mint in ((0,token),(1,wsol)):
            metas=ixs[idx].get('accounts')
            if not isinstance(metas,(list,tuple)) or len(metas)<6:
                raise RuntimeError('ORACLE175_ATA_METAS_INCOMPLETE')
            if _oracle175_pub(metas[3])!=mint:
                raise RuntimeError('ORACLE175_WRONG_ATA_MINT')
            if _oracle175_pub(metas[0])!=_oracle175_pub(metas[2]):
                raise RuntimeError('ORACLE175_ATA_PAYER_OWNER_MISMATCH')
            ata_destination=_oracle175_pub(metas[1])
            if not ata_destination or not _oracle175_pub(metas[5]):
                raise RuntimeError('ORACLE175_ATA_DEST_OR_PROGRAM_MISSING')
            addresses.append(ata_destination)
        if addresses[0]==addresses[1]:
            raise RuntimeError('ORACLE175_ATA_DEST_COLLISION')
        if programs.count(pump)!=1 or programs.count(meteora_id)!=1:
            raise RuntimeError('ORACLE175_EXACT_TWO_LEGS_MISSING')
        if direction=='PUMP_TO_METEORA' and programs.index(pump)>programs.index(meteora_id):
            raise RuntimeError('ORACLE175_WRONG_FORWARD_ORDER')
        if direction=='METEORA_TO_PUMP' and programs.index(meteora_id)>programs.index(pump):
            raise RuntimeError('ORACLE175_WRONG_REVERSE_ORDER')
        pump_ix=ixs[programs.index(pump)]
        pump_keys={_oracle175_pub(m) for m in pump_ix.get('accounts',[])}
        if addresses[0] not in pump_keys:
            raise RuntimeError('ORACLE175_PUMP_USER_TOKEN_ATA_UNREFERENCED')
    return True

def _fast_010_profit_lock_route(route,direction,required_final_out):
    result=_ORACLE175_PREVIOUS_LOCK(route,direction,required_final_out)
    if not isinstance(result,tuple) or len(result)!=3:
        raise RuntimeError('ORACLE175_PROFIT_LOCK_SHAPE')
    _oracle175_check(result[0],direction)
    return result
'''

def test():
    ast.parse(BLOCK)
    env={'_fast_010_profit_lock_route':lambda r,d,m:(r,1,2)}
    exec(BLOCK,env)
    def meta(x):return {'pubkey':x}
    token='TokenMint'
    wsol='So11111111111111111111111111111111111111112'
    ata='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
    def ata_ix(mint,dst):
        return {'programId':ata,'accounts':[
            meta('wallet'),meta(dst),meta('wallet'),
            meta(mint),meta('system'),meta('token_program')]}
    pump={'programId':'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA',
          'accounts':[meta('token_ata')]}
    meteor={'programId':'METEORA','accounts':[]}
    good={'token':token,'meteora_ix':meteor,'original_candidates':[
        ('ATA_READY',[ata_ix(token,'token_ata'),ata_ix(wsol,'wsol_ata'),pump,meteor])]}
    assert env['_oracle175_check'](good,'PUMP_TO_METEORA')
    broken={'token':token,'meteora_ix':meteor,'original_candidates':[
        ('A',[ata_ix(wsol,'token_ata'),ata_ix(token,'wsol_ata'),pump,meteor])]}
    try:
        env['_oracle175_check'](broken,'PUMP_TO_METEORA')
    except RuntimeError:pass
    else:raise AssertionError('wrong ATA mint accepted')
    print('[TEST PASS] ORACLE175 ATA mint, owner/payer, destinations, direction, both legs')

def install():
    if not TARGET.is_file():raise RuntimeError('HOLD_ORACLE175_RUNTIME_NOT_FOUND')
    install_block('ORACLE175',MARK,BLOCK,
        ('ORACLE174_EXACT_QUOTE_GATE','ORACLE166C_FORWARD_ATA_READINESS'))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    a=p.parse_args()
    test() if a.test else install()
