"""Align existing SDK WSOL funding to the exact forward swap budget."""
import base64
import copy
import struct

SYSTEM = '11111111111111111111111111111111'
TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
ALLOWED = {10_000_000, 15_000_000, 20_000_000, 25_000_000, 30_000_000}


def key(row):
    return str((row or {}).get('pubkey') or '')


def align(ixs, user, wsol_ata, spend, pump_program):
    """Rewrite exactly one System Transfer into WSOL ATA; require SyncNative."""
    if type(spend) is not int or spend not in ALLOWED:
        raise RuntimeError('ORACLE087_SIZE_NOT_ADMITTED')
    out = copy.deepcopy(ixs)
    transfers = []
    syncs = []
    pumps = []
    for n, ix in enumerate(out):
        program = str(ix.get('programId') or '')
        accounts = list(ix.get('accounts') or [])
        try:
            raw = base64.b64decode(ix.get('data') or '', validate=True)
        except Exception as exc:
            raise RuntimeError('ORACLE087_BAD_INSTRUCTION_DATA') from exc
        if program == SYSTEM and len(raw) == 12 and raw[:4] == struct.pack('<I', 2):
            if len(accounts) >= 2 and key(accounts[0]) == user and key(accounts[1]) == wsol_ata:
                transfers.append((n, raw))
        if program == TOKEN and raw == b'\x11' and accounts and key(accounts[0]) == wsol_ata:
            syncs.append(n)
        if program == str(pump_program) and any(key(a) == wsol_ata for a in accounts):
            pumps.append(n)
    if len(transfers) != 1:
        raise RuntimeError('ORACLE087_EXACT_WSOL_FUNDING_TRANSFER_COUNT:'+str(len(transfers)))
    pos, raw = transfers[0]
    if len(syncs) != 1 or syncs[0] <= pos:
        raise RuntimeError('ORACLE087_SYNC_NATIVE_MISSING_OR_MISORDERED')
    # PumpSwap must consume the same ATA, after SyncNative.
    if not any(i > syncs[0] for i in pumps):
        raise RuntimeError('ORACLE087_NO_POST_SYNC_SWAP_ACCOUNT_MATCH')
    out[pos]['data'] = base64.b64encode(raw[:4] + struct.pack('<Q', spend)).decode()
    assert struct.unpack('<Q', base64.b64decode(out[pos]['data'])[4:12])[0] == spend
    return out


def route_funding(route, user, q87):
    if route.get('direction') != 'PUMP_TO_METEORA':
        return route
    spend = route.get('start_lamports')
    ata = str(q87.c.ata(user, q87.c.WSOL, q87.c.TOKEN))
    candidates = list(route.get('original_candidates') or [])
    if not candidates:
        raise RuntimeError('ORACLE087_NO_FORWARD_CANDIDATES')
    result = dict(route)
    result['original_candidates'] = [
        (name, align(ixs, str(user), ata, spend, q87.c.PUMP)) for name, ixs in candidates
    ]
    result['oracle087_wsol_funding_aligned'] = True
    return result
