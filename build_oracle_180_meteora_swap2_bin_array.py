
"""ORACLE180: Guarded Meteora Swap2 named-account/bin-array repair."""
import argparse, ast, os
from pathlib import Path

TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
MARK='# ORACLE180_SWAP2_BIN_ARRAY_CORRECTION'
BLOCK='''# ORACLE180_SWAP2_BIN_ARRAY_CORRECTION
_ORACLE180_PREVIOUS_LOCK=_fast_010_profit_lock_route

def _oracle180_repair(route,direction):
    import base64 as _b64, copy as _copy
    dlmm='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
    memo='MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
    disc=bytes([65,75,63,76,235,91,91,136])
    token=str(route.get('token') or '')
    template=METEORA_TEMPLATES.get(token)
    if not isinstance(template,dict):raise RuntimeError('ORACLE180_NO_WARM_TEMPLATE')
    fixed=template.get('fixed_accounts')
    arrays=template.get('arrays')
    if not isinstance(fixed,list) or len(fixed) not in (15,16):
        raise RuntimeError('ORACLE180_TEMPLATE_LAYOUT_UNKNOWN')
    if not isinstance(arrays,list) or not arrays:
        raise RuntimeError('ORACLE180_NO_WARM_BIN_ARRAYS')
    allowed=set()
    for item in arrays:
        if not isinstance(item,(list,tuple)) or len(item)<2:
            raise RuntimeError('ORACLE180_ARRAY_DESCRIPTOR_UNKNOWN')
        allowed.add(str(item[1]))
    old=route.get('meteora_ix')
    if not isinstance(old,dict) or old.get('programId')!=dlmm:
        raise RuntimeError('ORACLE180_DLMM_INSTRUCTION_UNKNOWN')
    raw=_b64.b64decode(old.get('data') or '',validate=True)
    if len(raw)<25 or raw[:8]!=disc:
        raise RuntimeError('ORACLE180_NOT_SWAP2_WITH_REMAINING_INFO')
    accounts=_copy.deepcopy(old.get('accounts'))
    if not isinstance(accounts,list) or len(accounts)<16:
        raise RuntimeError('ORACLE180_ACCOUNTS_SHORT')
    def key(i):return str(accounts[i].get('pubkey',''))
    if key(0)!=str(template.get('pool') or ''):
        raise RuntimeError('ORACLE180_POOL_IDENTITY_MISMATCH')
    event=str(fixed[13][0])
    if key(13)==event and key(14)==dlmm:
        accounts.insert(13,{'pubkey':memo,'isSigner':False,'isWritable':False})
    elif not (key(13)==memo and key(14)==event and key(15)==dlmm):
        raise RuntimeError('ORACLE180_UNRECOGNIZED_NAMED_ACCOUNT_ORDER')
    if len(accounts)<17 or key(15)!=dlmm:
        raise RuntimeError('ORACLE180_BIN_ARRAY_ABSENT')
    tail=accounts[16:]
    if not tail or any(not isinstance(m,dict) or
           str(m.get('pubkey','')) not in allowed or
           m.get('isWritable') is not True or
           m.get('isSigner') is True for m in tail):
        raise RuntimeError('ORACLE180_BIN_ARRAY_NOT_WARM_VERIFIED')
    if len(set(str(m['pubkey']) for m in tail))!=len(tail):
        raise RuntimeError('ORACLE180_DUPLICATE_BIN_ARRAY')
    corrected=_copy.deepcopy(old)
    corrected['accounts']=accounts
    out=dict(route)
    out['meteora_ix']=corrected
    candidates=[]
    for name,ixs in route.get('original_candidates') or []:
        positions=[i for i,ix in enumerate(ixs) if ix.get('programId')==dlmm]
        if len(positions)!=1:raise RuntimeError('ORACLE180_CANDIDATE_DLMM_COUNT')
        if ixs[positions[0]].get('data')!=old.get('data'):
            raise RuntimeError('ORACLE180_CANDIDATE_SWAP_DATA_DRIFT')
        newixs=[_copy.deepcopy(ix) for ix in ixs]
        newixs[positions[0]]=_copy.deepcopy(corrected)
        candidates.append((name,newixs))
    if not candidates:raise RuntimeError('ORACLE180_NO_CANDIDATES')
    out['original_candidates']=candidates
    print('[ORACLE180_SWAP2_LAYOUT] direction=%s named=16 bin_arrays=%d broadcast=FALSE' %
          (direction,len(tail)),flush=True)
    return out

def _fast_010_profit_lock_route(route,direction,required_final_out):
    result=_ORACLE180_PREVIOUS_LOCK(route,direction,required_final_out)
    if not isinstance(result,tuple) or len(result)!=3:
        raise RuntimeError('ORACLE180_PROFIT_LOCK_RESULT_CHANGED')
    return (_oracle180_repair(result[0],direction),result[1],result[2])
'''

def inject(src):
    for x in ('# ORACLE175_ATA_ACCOUNT_IDENTITY',
              'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
              'def _fast_010_profit_lock_route('):
        if x not in src:raise RuntimeError('HOLD_ORACLE180_MISSING_CONTRACT:'+x[:35])
    if MARK in src:
        if src.count(MARK)!=1:raise RuntimeError('HOLD_ORACLE180_DUPLICATE')
        ast.parse(src);return src,False
    tree=ast.parse(src)
    runs=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run']
    if len(runs)!=1:raise RuntimeError('HOLD_ORACLE180_RUN_BOUNDARY_DRIFT')
    lines=src.splitlines(keepends=True)
    i=runs[0].lineno-1
    updated=''.join(lines[:i])+BLOCK+'\n'+''.join(lines[i:])
    ast.parse(updated)
    return updated,True

def test():
    ast.parse(BLOCK)
    import base64
    dlmm='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
    event='event_authority'
    fixed=[('a',False,False)]*13+[(event,False,False),(dlmm,False,False)]
    program={'programId':dlmm,'data':base64.b64encode(bytes([65,75,63,76,235,91,91,136])+bytes(17)).decode(),
             'accounts':[{'pubkey':v[0],'isSigner':v[1],'isWritable':v[2]} for v in fixed]+[
             {'pubkey':'warm_bin','isSigner':False,'isWritable':True}]}
    row={'token':'t','meteora_ix':program,'original_candidates':[('N',[program])]}
    env={'_fast_010_profit_lock_route':lambda r,d,m:(r,0,m),
         'METEORA_TEMPLATES':{'t':{'pool':'a','fixed_accounts':fixed,'arrays':[(0,'warm_bin')]}}}
    exec(BLOCK,env)
    out=env['_fast_010_profit_lock_route'](row,'METEORA_TO_PUMP',100)[0]
    assert len(out['meteora_ix']['accounts'])==17
    assert out['original_candidates'][0][1][0]['accounts'][13]['pubkey'].startswith('Memo')
    assert len(env['_oracle180_repair'](out,'METEORA_TO_PUMP')['meteora_ix']['accounts'])==17
    for bad in ('missing','untrusted'):
        changed=dict(row)
        changed['meteora_ix']=dict(program)
        changed['meteora_ix']['accounts']=[dict(a) for a in program['accounts']]
        changed['meteora_ix']['accounts'][-1]['pubkey']=bad
        try:env['_oracle180_repair'](changed,'METEORA_TO_PUMP')
        except RuntimeError:pass
        else:raise AssertionError('untrusted array accepted')
    print('[TEST PASS] ORACLE180 Swap2 16 named accounts, warm bins, candidate binding, fail-closed')

def install():
    if not TARGET.is_file():raise RuntimeError('HOLD_ORACLE180_RUNTIME_NOT_FOUND')
    source=TARGET.read_text(encoding='utf-8')
    updated,change=inject(source)
    if not change:print('[INSTALL PASS] ORACLE180 already installed');return
    backup=TARGET.with_name('runtime.before_oracle180.py')
    if backup.exists() and backup.read_text(encoding='utf-8')!=source:
        raise RuntimeError('HOLD_ORACLE180_BACKUP_COLLISION')
    if not backup.exists():backup.write_text(source,encoding='utf-8')
    temp=TARGET.with_name('runtime.oracle180.pending')
    if temp.exists():raise RuntimeError('HOLD_ORACLE180_PENDING_COLLISION')
    try:
        temp.write_text(updated,encoding='utf-8')
        ast.parse(temp.read_text(encoding='utf-8'))
        os.replace(temp,TARGET)
    finally:
        if temp.exists():temp.unlink()
    print('[INSTALL PASS] ORACLE180 Meteora Swap2 account layout; scanner untouched; broadcast blocked')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true')
    a=p.parse_args();test() if a.test else install()
