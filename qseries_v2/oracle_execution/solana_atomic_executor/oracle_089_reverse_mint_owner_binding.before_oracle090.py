"""ORACLE-089: verify actual Solana mint owners before binding DLMM token program slots."""
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
