"""ORACLE-090 complete installer: legacy DLMM swap -> verified Swap2 reverse route."""
import argparse
import ast
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'oracle_089_reverse_mint_owner_binding.py'
BACKUP = ROOT / 'oracle_089_reverse_mint_owner_binding.before_oracle090.py'
MARK = 'ORACLE090_LEGACY_SWAP2_NORMALIZATION'
SOURCE = r'''"""ORACLE090_LEGACY_SWAP2_NORMALIZATION: read-only mint owner, exact reverse DLMM normalization."""
import base64
import copy
import json
import os
import struct
import urllib.request

TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
SWAP = bytes([248,198,158,145,225,117,135,200])
SWAP2 = bytes([65,75,63,76,235,91,91,136])
MEMO = 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
_CACHE = {}

def owner_of_mint(mint):
    if mint in _CACHE:
        return _CACHE[mint]
    url = os.environ.get('SOLANA_RPC_URL', '').strip()
    if not url.startswith('https://'):
        raise RuntimeError('ORACLE090_HOLD_HTTPS_SOLANA_RPC_UNAVAILABLE')
    req = urllib.request.Request(url, data=json.dumps({
        'jsonrpc':'2.0','id':1,'method':'getAccountInfo',
        'params':[mint,{'encoding':'base64','commitment':'processed'}]
    }).encode(), headers={'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req,timeout=6) as response:
            reply=json.loads(response.read(200000))
    except Exception as exc:
        raise RuntimeError('ORACLE090_HOLD_MINT_OWNER_RPC_'+type(exc).__name__) from None
    record=(reply.get('result') or {}).get('value') if not reply.get('error') else None
    if not record or record.get('executable') is not False:
        raise RuntimeError('ORACLE090_HOLD_MINT_ACCOUNT_NOT_VERIFIED')
    owner=str(record.get('owner') or '')
    if owner not in (TOKEN,TOKEN22):
        raise RuntimeError('ORACLE090_HOLD_UNEXPECTED_MINT_OWNER')
    _CACHE[mint]=owner
    return owner

def bind(route,wsol,resolve=owner_of_mint):
    if route.get('direction')!='METEORA_TO_PUMP':
        raise RuntimeError('ORACLE090_HOLD_DIRECTION')
    token=str(route.get('token') or '')
    wsol=str(wsol)
    if not token or token==wsol:
        raise RuntimeError('ORACLE090_HOLD_TOKEN_IDENTITY')
    original=copy.deepcopy(list(route.get('original_candidates') or []))
    if not original:
        raise RuntimeError('ORACLE090_HOLD_CANDIDATES_EMPTY')
    owners={token:resolve(token),wsol:resolve(wsol)}
    if any(v not in (TOKEN,TOKEN22) for v in owners.values()):
        raise RuntimeError('ORACLE090_HOLD_UNKNOWN_MINT_OWNER')
    out=copy.deepcopy(route)
    converted=0
    rebound=[]
    for name,ixs in original:
        found=[ix for ix in ixs if ix.get('programId')==DLMM]
        if len(found)!=1:
            raise RuntimeError('ORACLE090_HOLD_NOT_ONE_DLMM_LEG')
        ix=found[0]
        ac=ix.get('accounts') or []
        if len(ac)<15:
            raise RuntimeError('ORACLE090_HOLD_ACCOUNT_LAYOUT_SHORT')
        try:
            raw=base64.b64decode(ix.get('data') or '',validate=True)
        except Exception:
            raise RuntimeError('ORACLE090_HOLD_INVALID_SWAP_DATA') from None
        if raw[:8]==SWAP:
            if len(raw)!=24 or len(ac)!=15:
                raise RuntimeError('ORACLE090_HOLD_LEGACY_LAYOUT_UNVERIFIED')
            if str(ac[14].get('pubkey') or '')!=DLMM:
                raise RuntimeError('ORACLE090_HOLD_LEGACY_DLMM_PROGRAM_SLOT')
            ac.insert(13,{'pubkey':MEMO,'isSigner':False,'isWritable':False})
            raw=SWAP2+raw[8:24]+struct.pack('<I',0)
            ix['data']=base64.b64encode(raw).decode()
            converted+=1
        elif raw[:8]==SWAP2:
            if len(ac)<16 or len(raw)<28:
                raise RuntimeError('ORACLE090_HOLD_SWAP2_LAYOUT_UNVERIFIED')
            if str(ac[13].get('pubkey') or '')!=MEMO:
                raise RuntimeError('ORACLE090_HOLD_SWAP2_MEMO_MISMATCH')
        else:
            raise RuntimeError('ORACLE090_HOLD_UNKNOWN_SWAP_DISCRIMINATOR')
        x=str(ac[6].get('pubkey') or '')
        y=str(ac[7].get('pubkey') or '')
        if {x,y}!={token,wsol}:
            raise RuntimeError('ORACLE090_HOLD_MINT_LAYOUT_MISMATCH')
        for index,mint in ((11,x),(12,y)):
            if ac[index].get('isSigner') or ac[index].get('isWritable'):
                raise RuntimeError('ORACLE090_HOLD_PROGRAM_META_FLAGS')
            ac[index]['pubkey']=owners[mint]
        rebound.append((name,ixs))
    out['original_candidates']=rebound
    # Preserve the exact normalized DLMM instruction for downstream consumers.
    out['meteora_ix']=copy.deepcopy(next(ix for ix in rebound[0][1] if ix.get('programId')==DLMM))
    out['oracle089_mint_owner_verified']=True
    out['oracle090_normalized_legacy_count']=converted
    print('[ORACLE090_BOUND] direction=METEORA_TO_PUMP candidates=%d converted=%d token_program=%s wsol_program=%s' %
          (len(rebound),converted,owners[token],owners[wsol]),flush=True)
    return out
'''

def test():
    import base64
    import types
    ast.parse(SOURCE)
    obj=types.ModuleType('oracle090_fixture')
    exec(compile(SOURCE,'<oracle090>','exec'),obj.__dict__)
    def sample(legacy=True):
        ac=[{'pubkey':'acc'+str(i),'isSigner':False,'isWritable':False} for i in range(15 if legacy else 16)]
        ac[6]['pubkey']='mint'; ac[7]['pubkey']='wsol'
        ac[11]['pubkey']=obj.TOKEN; ac[12]['pubkey']=obj.TOKEN22
        if legacy: ac[14]['pubkey']=obj.DLMM
        else: ac[13]['pubkey']=obj.MEMO
        raw=(obj.SWAP+b'12345678abcdefgh') if legacy else (obj.SWAP2+b'12345678abcdefgh'+bytes(4))
        return {'programId':obj.DLMM,'accounts':ac,'data':base64.b64encode(raw).decode()}
    def route(legacy=True):
        ix=sample(legacy)
        return {'token':'mint','direction':'METEORA_TO_PUMP','original_candidates':[('REVERSE_FULL_NATIVE',[{'programId':'ATA'},ix,{'programId':'PUMP'}])]}
    owners=lambda m:{'mint':obj.TOKEN22,'wsol':obj.TOKEN}[m]
    for legacy in (True,False):
        before=route(legacy)
        after=obj.bind(before,'wsol',owners)
        ix=after['original_candidates'][0][1][1]
        assert len(ix['accounts'])==16
        assert ix['accounts'][11]['pubkey']==obj.TOKEN22
        assert ix['accounts'][12]['pubkey']==obj.TOKEN
        assert ix['accounts'][13]['pubkey']==obj.MEMO
        assert base64.b64decode(ix['data'])[:8]==obj.SWAP2
        assert after['oracle090_normalized_legacy_count']==int(legacy)
        assert len(before['original_candidates'][0][1][1]['accounts'])==(15 if legacy else 16)
    bad=route(True)
    bad['original_candidates'][0][1][1]['accounts'][14]['pubkey']='WRONG'
    try:
        obj.bind(bad,'wsol',owners)
        raise AssertionError('Expected legacy account program slot hold')
    except RuntimeError as exc:
        assert 'ORACLE090_HOLD_LEGACY_DLMM_PROGRAM_SLOT' in str(exc)
    bad=route(True)
    bad['original_candidates'][0][1][1]['accounts'][6]['pubkey']='WRONG'
    try:
        obj.bind(bad,'wsol',owners)
        raise AssertionError('Expected mint layout hold')
    except RuntimeError as exc:
        assert 'ORACLE090_HOLD_MINT_LAYOUT_MISMATCH' in str(exc)
    assert TARGET.exists(), 'ORACLE089 module missing'
    s=TARGET.read_text(encoding='utf-8')
    assert 'def bind(' in s
    reverse=(ROOT/'oracle_054_reverse_native_handoff.py').read_text(encoding='utf-8')
    assert '# ORACLE089_REVERSE_MINT_OWNER_CUTOVER' in reverse
    assert '# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_BEGIN' in reverse
    print('[PASS] ORACLE090_LEGACY_AND_SWAP2_OWNER_BINDING_TESTS')
    print('[BOUNDARY] NO_PRIVATE_KEY NO_SIGNING NO_BROADCAST NO_SCANNER_EDIT')

def install():
    test()
    existing=TARGET.read_text(encoding='utf-8')
    if MARK in existing:
        print('[PASS] ORACLE090_ALREADY_INSTALLED')
        return
    if BACKUP.exists():
        raise RuntimeError('ORACLE090_BACKUP_ALREADY_EXISTS')
    ast.parse(SOURCE)
    BACKUP.write_text(existing,encoding='utf-8')
    TARGET.write_text(SOURCE,encoding='utf-8')
    print('[PASS] ORACLE090_REVERSE_SWAP2_NORMALIZATION_INSTALLED')
    print('[BACKUP]',BACKUP)
    print('[SCOPE] EXISTING_ORACLE089_WRAPPER_REUSED; NO_SIGNING NO_BROADCAST')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    a=ap.parse_args()
    test() if a.test else install()
