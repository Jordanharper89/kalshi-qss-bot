"""ORACLE-089 complete reverse DLMM mint-owner binding installer.
Only reverse native route; no scanner, signing, broadcast, ALT mutation.
"""
import argparse
import ast
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'oracle_054_reverse_native_handoff.py'
MODULE = ROOT / 'oracle_089_reverse_mint_owner_binding.py'
MARK = '# ORACLE089_REVERSE_MINT_OWNER_CUTOVER'
SOURCE = r'''"""ORACLE-089: verify actual Solana mint owners before binding DLMM token program slots."""
import copy
import json
import os
import urllib.request

TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
SWAP2 = bytes([65,75,63,76,235,91,91,136])
_CACHE = {}


def owner_of_mint(mint):
    """One read-only account lookup per unique mint in this process; no secret output."""
    if mint in _CACHE:
        return _CACHE[mint]
    url = os.environ.get('SOLANA_RPC_URL', '').strip()
    if not url.startswith('https://'):
        raise RuntimeError('ORACLE089_HOLD_HTTPS_SOLANA_RPC_UNAVAILABLE')
    request = urllib.request.Request(url, data=json.dumps({
        'jsonrpc':'2.0', 'id':1, 'method':'getAccountInfo',
        'params':[mint, {'encoding':'base64', 'commitment':'processed'}]
    }).encode(), headers={'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            reply = json.loads(response.read(200000))
    except Exception as exc:
        # Never surface HTTP request URLs (they can include the RPC API key).
        raise RuntimeError('ORACLE089_HOLD_MINT_OWNER_RPC_'+type(exc).__name__) from None
    if reply.get('error') or not (reply.get('result') or {}).get('value'):
        raise RuntimeError('ORACLE089_HOLD_MINT_ACCOUNT_NOT_VERIFIED')
    record = reply['result']['value']
    owner = str(record.get('owner') or '')
    if not record.get('executable') is False or owner not in (TOKEN,TOKEN22):
        raise RuntimeError('ORACLE089_HOLD_MINT_OWNER_NOT_TOKEN_PROGRAM')
    _CACHE[mint] = owner
    return owner


def bind(route, wsol, resolve=owner_of_mint):
    if route.get('direction') != 'METEORA_TO_PUMP':
        raise RuntimeError('ORACLE089_HOLD_DIRECTION')
    token = str(route.get('token') or '')
    if not token or token == str(wsol):
        raise RuntimeError('ORACLE089_HOLD_TOKEN_IDENTITY')
    out = copy.deepcopy(route)
    original = list(out.get('original_candidates') or [])
    if not original:
        raise RuntimeError('ORACLE089_HOLD_CANDIDATES_EMPTY')
    resolved = {token:resolve(token), str(wsol):resolve(str(wsol))}
    if any(v not in (TOKEN,TOKEN22) for v in resolved.values()):
        raise RuntimeError('ORACLE089_HOLD_UNKNOWN_MINT_OWNER')
    for _, ixs in original:
        dlmm = [i for i in ixs if i.get('programId') == DLMM]
        if len(dlmm) != 1:
            raise RuntimeError('ORACLE089_HOLD_NOT_ONE_DLMM_LEG')
        ix = dlmm[0]
        accounts = ix.get('accounts') or []
        if len(accounts) < 16:
            raise RuntimeError('ORACLE089_HOLD_SWAP2_ACCOUNT_LAYOUT')
        import base64
        try:
            raw = base64.b64decode(ix.get('data') or '', validate=True)
        except Exception:
            raise RuntimeError('ORACLE089_HOLD_INVALID_SWAP_DATA') from None
        if raw[:8] != SWAP2:
            raise RuntimeError('ORACLE089_HOLD_NOT_SWAP2')
        x = str(accounts[6].get('pubkey') or '')
        y = str(accounts[7].get('pubkey') or '')
        if {x,y} != {token,str(wsol)}:
            raise RuntimeError('ORACLE089_HOLD_MINT_LAYOUT_MISMATCH')
        # Both programs are bound to the verified owners of their respective mints.
        accounts[11]['pubkey'] = resolved[x]
        accounts[12]['pubkey'] = resolved[y]
        if accounts[11].get('isSigner') or accounts[12].get('isSigner'):
            raise RuntimeError('ORACLE089_HOLD_PROGRAM_ACCOUNT_SIGNER')
    out['original_candidates'] = original
    out['oracle089_mint_owner_verified'] = True
    print('[ORACLE089_BOUND] direction=METEORA_TO_PUMP candidates=%d token_program=%s wsol_program=%s' %
          (len(original), resolved[token], resolved[str(wsol)]), flush=True)
    return out
'''
WRAPPER = '''\n# ORACLE089_REVERSE_MINT_OWNER_CUTOVER
_ORACLE089_PREVIOUS_NATIVE_REVERSE_ROUTE = native_reverse_route

def native_reverse_route(snap, row, templates, rt, q18, fee_bps=20, reserve=100000):
    from .oracle_089_reverse_mint_owner_binding import bind
    route = _ORACLE089_PREVIOUS_NATIVE_REVERSE_ROUTE(
        snap, row, templates, rt, q18, fee_bps, reserve)
    return bind(route, str(rt.q87.c.WSOL))
'''

def test():
    import base64
    import types
    import sys
    ast.parse(SOURCE)
    ast.parse(WRAPPER)
    obj = types.ModuleType('oracle089_offline_fixture')
    exec(compile(SOURCE, '<oracle089>', 'exec'), obj.__dict__)
    def ix(mint_x='mintA', mint_y='wsol'):
        ac = [{'pubkey':'account'+str(j), 'isSigner':False} for j in range(16)]
        ac[6]['pubkey'] = mint_x
        ac[7]['pubkey'] = mint_y
        ac[11]['pubkey'] = obj.TOKEN22  # deliberately incorrect
        ac[12]['pubkey'] = obj.TOKEN22  # deliberately incorrect
        return {'programId':obj.DLMM, 'accounts':ac,
                'data':base64.b64encode(obj.SWAP2+b'12345678901234567890').decode()}
    row = {'token':'mintA', 'direction':'METEORA_TO_PUMP',
           'original_candidates':[('REVERSE_FULL_NATIVE', [ix()])]}
    got = obj.bind(row, 'wsol', lambda mint: {'mintA':obj.TOKEN22,'wsol':obj.TOKEN}[mint])
    ac = got['original_candidates'][0][1][0]['accounts']
    assert ac[11]['pubkey'] == obj.TOKEN22 and ac[12]['pubkey'] == obj.TOKEN
    assert row['original_candidates'][0][1][0]['accounts'][12]['pubkey'] == obj.TOKEN22
    bad = copy_row = {'token':'mintA','direction':'METEORA_TO_PUMP',
                       'original_candidates':[('BAD',[ix('other','wsol')])]}
    try:
        obj.bind(bad,'wsol',lambda m: obj.TOKEN)
        raise AssertionError('Expected mint mismatch hold')
    except RuntimeError as exc:
        assert 'ORACLE089_HOLD_MINT_LAYOUT_MISMATCH' in str(exc)
    assert TARGET.is_file(), 'Native reverse module missing'
    s = TARGET.read_text(encoding='utf-8')
    assert 'def native_reverse_route(' in s
    assert '# ORACLE085_REVERSE_EXACT_ATA_CUTOVER_BEGIN' in s, 'ORACLE085 missing'
    print('[PASS] ORACLE089_OFFLINE_OWNER_BINDING_AND_FAIL_CLOSED')
    print('[BOUNDARY] READ_ONLY_GETACCOUNTINFO; NO_SIGNING NO_BROADCAST NO_SCANNER_EDIT')


def install():
    test()
    original = TARGET.read_text(encoding='utf-8')
    if MARK in original:
        assert MODULE.is_file(), 'Installed wrapper missing helper'
        print('[PASS] ORACLE089_ALREADY_INSTALLED')
        return
    if MODULE.exists():
        raise RuntimeError('ORACLE089_HELPER_ALREADY_EXISTS_UNEXPECTEDLY')
    backup = TARGET.with_name(TARGET.stem + '.before_oracle089.py')
    if backup.exists():
        raise RuntimeError('ORACLE089_BACKUP_ALREADY_EXISTS')
    # Add after ORACLE085's wrapper; all calls from imported runtime see it.
    updated = original.rstrip() + '\n' + WRAPPER + '\n'
    ast.parse(updated)
    backup.write_text(original, encoding='utf-8')
    MODULE.write_text(SOURCE, encoding='utf-8')
    TARGET.write_text(updated, encoding='utf-8')
    print('[PASS] ORACLE089_REVERSE_MINT_OWNER_BINDING_INSTALLED')
    print('[BACKUP]',backup)
    print('[SCOPE] REVERSE_NATIVE_ONLY; NO_SECRET_PRINTING NO_SIGNING NO_BROADCAST')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--test',action='store_true')
    test() if args.parse_args().test else install()
