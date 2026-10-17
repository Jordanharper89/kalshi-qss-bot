"""ORACLE-087 full installer: fail-closed forward WSOL funding alignment."""
import argparse
import ast
from pathlib import Path

PKG = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = PKG / 'runtime.py'
HELPER = PKG / 'oracle_087_wsol_funding_alignment.py'
MARK = '# ORACLE087_FORWARD_WSOL_FUNDING_CUTOVER'
MODULE = r'''"""Align existing SDK WSOL funding to the exact forward swap budget."""
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
'''
CUTOVER = '''\n\n# ORACLE087_FORWARD_WSOL_FUNDING_CUTOVER\n_oracle087_previous_same_snapshot_route = same_snapshot_route\ndef same_snapshot_route(user, snap, opportunity):\n    from .oracle_087_wsol_funding_alignment import route_funding\n    route = _oracle087_previous_same_snapshot_route(user, snap, opportunity)\n    return route_funding(route, user, q87)\n'''


def tests():
    import base64, struct, sys, types
    mod = types.ModuleType('oracle087_test')
    exec(compile(MODULE, '<oracle087>', 'exec'), mod.__dict__)
    user, ata = 'user', 'wsol_ata'
    def ix(p, accounts, raw):
        return {'programId':p, 'accounts':[{'pubkey':x} for x in accounts], 'data':base64.b64encode(raw).decode()}
    rows = [ix(mod.SYSTEM,[user,ata],struct.pack('<IQ',2,10_000_000)),
            ix(mod.TOKEN,[ata],b'\x11'),ix('pump',[ata],b'abc')]
    for spend in sorted(mod.ALLOWED):
        out = mod.align(rows,user,ata,spend,'pump')
        assert struct.unpack('<Q',base64.b64decode(out[0]['data'])[4:])[0] == spend
        assert struct.unpack('<Q',base64.b64decode(rows[0]['data'])[4:])[0] == 10_000_000
    for broken in (rows[:1]+rows[2:], rows[1:], rows[:2]):
        try: mod.align(broken,user,ata,10_000_000,'pump')
        except RuntimeError: pass
        else: raise AssertionError('Unsafe funding path admitted')
    print('[PASS] ORACLE087_FIVE_SIZES_AND_FAIL_CLOSED_ORDERING')


def install():
    if not TARGET.is_file():
        raise SystemExit('[HOLD] CANONICAL_RUNTIME_NOT_FOUND')
    source = TARGET.read_text(encoding='utf-8')
    if MARK in source:
        print('[PASS] ORACLE087_ALREADY_INSTALLED')
        return
    if 'def same_snapshot_route(' not in source or 'q87' not in source:
        raise SystemExit('[HOLD] RUNTIME_CONTRACT_MISSING')
    ast.parse(source)
    ast.parse(MODULE)
    updated = source + CUTOVER
    ast.parse(updated)
    backup = TARGET.with_name('runtime.before_oracle087.py')
    if backup.exists():
        raise SystemExit('[HOLD] BACKUP_ALREADY_EXISTS_WITHOUT_CUTOVER')
    backup.write_text(source, encoding='utf-8')
    HELPER.write_text(MODULE, encoding='utf-8')
    TARGET.write_text(updated, encoding='utf-8')
    print('[PASS] ORACLE087_FORWARD_WSOL_FUNDING_CUTOVER_INSTALLED')
    print('[BACKUP]',backup)
    print('[BOUNDARY] UNSUPPORTED_SDK_FUNDING_LAYOUT_HOLDS; NO_SIGNING NO_BROADCAST')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    args = p.parse_args()
    tests()
    if not args.test: install()
