"""ORACLE-235M V3: complete read-only PumpSwap vault identity and account check."""
import argparse
import base64
import hashlib
import json
import os
import struct
import urllib.request
from pathlib import Path

from solders.pubkey import Pubkey

ROOT = Path('runtime_state/oracle/oracle_live_execution')
REPORT = ROOT / 'ORACLE235M_VERIFIED_VAULTS.json'
PUMP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
LEGACY = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
WSOL = 'So11111111111111111111111111111111111111112'
POOL_DISC = hashlib.sha256(b'account:Pool').digest()[:8]


def key(raw):
    raw = bytes(raw)
    if len(raw) != 32:
        raise ValueError('INVALID_PUBKEY_LENGTH')
    return str(Pubkey.from_bytes(raw))


def pool_fields(raw):
    raw = bytes(raw)
    if len(raw) < 203 or raw[:8] != POOL_DISC:
        raise ValueError('INVALID_PUMP_POOL_LAYOUT')
    return {'base_mint': key(raw[43:75]), 'quote_mint': key(raw[75:107]),
            'base_vault': key(raw[139:171]), 'quote_vault': key(raw[171:203])}


def token22_extensions(raw):
    if len(raw) == 165:
        return []
    if len(raw) < 166 or raw[165] != 2:
        raise ValueError('INVALID_TOKEN22_ACCOUNT_TYPE')
    found = []
    pos = 166
    while pos < len(raw):
        if not any(raw[pos:]):
            break
        if pos + 4 > len(raw):
            raise ValueError('TRUNCATED_TLV_HEADER')
        kind, length = struct.unpack_from('<HH', raw, pos)
        pos += 4
        if kind == 0 or kind in found or pos + length > len(raw):
            raise ValueError('INVALID_TLV_ENTRY')
        # ImmutableOwner (7) does not impose transfer restrictions.
        # Anything else needs an explicitly supported account-level audit.
        if kind != 7 or length != 0:
            raise ValueError('UNSUPPORTED_ACCOUNT_EXTENSION')
        found.append(kind)
        pos += length
    return found


def vault_check(entry, expected_mint, expected_program):
    if entry is None:
        return ['MISSING_VAULT'], {}
    owner_program, raw = entry
    raw = bytes(raw)
    problems = []
    if owner_program not in (LEGACY, TOKEN22) or owner_program != expected_program:
        problems.append('WRONG_TOKEN_PROGRAM')
    if len(raw) < 165:
        return problems + ['SHORT_TOKEN_ACCOUNT'], {}
    mint = key(raw[:32])
    authority = key(raw[32:64])
    amount = struct.unpack_from('<Q', raw, 64)[0]
    delegate = struct.unpack_from('<I', raw, 72)[0]
    state = raw[108]
    close = struct.unpack_from('<I', raw, 129)[0]
    if mint != expected_mint:
        problems.append('WRONG_VAULT_MINT')
    if state != 1:
        problems.append('FROZEN_OR_UNINITIALIZED')
    if amount <= 0:
        problems.append('EMPTY_VAULT')
    if delegate != 0:
        problems.append('DELEGATE_PRESENT')
    if close != 0:
        problems.append('CLOSE_AUTHORITY_PRESENT')
    extensions = []
    if owner_program == LEGACY and len(raw) != 165:
        problems.append('INVALID_LEGACY_LENGTH')
    elif owner_program == TOKEN22:
        try:
            extensions = token22_extensions(raw)
        except ValueError as exc:
            problems.append(str(exc))
    return sorted(set(problems)), {'mint': mint, 'balance_raw': amount,
                                   'authority': authority, 'extensions': extensions,
                                   'sha256': hashlib.sha256(raw).hexdigest()}


def fetch(addresses, url):
    if not addresses or len(addresses) > 100:
        raise ValueError('INVALID_ACCOUNT_BATCH')
    payload = json.dumps({'jsonrpc': '2.0', 'id': 23513,
                          'method': 'getMultipleAccounts',
                          'params': [addresses, {'encoding': 'base64',
                                                 'commitment': 'confirmed'}]}).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as response:
        body = json.load(response)
    if body.get('error'):
        raise RuntimeError('RPC_ACCOUNT_ERROR')
    result = body.get('result') or {}
    slot = (result.get('context') or {}).get('slot')
    values = result.get('value')
    if type(slot) is not int or slot <= 0 or not isinstance(values, list) or len(values) != len(addresses):
        raise RuntimeError('INVALID_ACCOUNT_RPC_RESPONSE')
    mapping = {}
    for address, item in zip(addresses, values):
        if item is None:
            mapping[address] = None
            continue
        data = item.get('data')
        if not isinstance(data, list) or len(data) != 2 or data[1] != 'base64':
            raise RuntimeError('INVALID_ACCOUNT_ENCODING')
        mapping[address] = (item.get('owner'), base64.b64decode(data[0], validate=True))
    return slot, mapping


def check_pair(pair, accounts):
    mint = str(pair.token)
    row = {'token': mint, 'status': 'HOLD', 'reasons': []}
    pool = accounts.get(str(pair.pump_pool))
    if pool is None or pool[0] != PUMP:
        row['reasons'].append('PUMP_POOL_OWNER_OR_ACCOUNT_INVALID')
        return row
    try:
        decoded = pool_fields(pool[1])
    except ValueError as exc:
        row['reasons'].append(str(exc))
        return row
    checks = {'base_mint': decoded['base_mint'] == mint,
              'quote_mint': decoded['quote_mint'] == WSOL,
              'base_vault': decoded['base_vault'] == str(pair.pump_base_vault),
              'quote_vault': decoded['quote_vault'] == str(pair.pump_quote_vault)}
    row['pool_checks'] = checks
    if not all(checks.values()):
        row['reasons'].append('POOL_IDENTITY_MISMATCH')
        return row
    mint_account = accounts.get(mint)
    sol_account = accounts.get(WSOL)
    if mint_account is None or sol_account is None:
        row['reasons'].append('MINT_ACCOUNT_MISSING')
        return row
    details = {}
    for side, vault_address, expected_mint, program in (
        ('base', decoded['base_vault'], mint, mint_account[0]),
        ('quote', decoded['quote_vault'], WSOL, sol_account[0])):
        problems, value = vault_check(accounts.get(vault_address), expected_mint, program)
        row['reasons'].extend(side.upper() + '_' + p for p in problems)
        details[side] = {'address': vault_address, 'data': value}
    row['vaults'] = details
    if not row['reasons']:
        row['status'] = 'PASS_POOL_VAULT_ACCOUNT_FIELDS'
    return row


def test():
    a, b, c, d = [bytes([n]) * 32 for n in (1, 2, 3, 4)]
    pool = bytearray(203)
    pool[:8] = POOL_DISC
    pool[43:75], pool[75:107] = a, b
    pool[139:171], pool[171:203] = c, d
    assert pool_fields(pool) == {'base_mint': key(a), 'quote_mint': key(b),
                                 'base_vault': key(c), 'quote_vault': key(d)}
    account = bytearray(165)
    account[:32] = a
    struct.pack_into('<Q', account, 64, 100)
    account[108] = 1
    assert not vault_check((LEGACY, account), key(a), LEGACY)[0]
    account[108] = 2
    assert 'FROZEN_OR_UNINITIALIZED' in vault_check((LEGACY, account), key(a), LEGACY)[0]
    account[108] = 1
    extended = account + bytes([2]) + struct.pack('<HH', 7, 0)
    assert not vault_check((TOKEN22, extended), key(a), TOKEN22)[0]
    assert vault_check((TOKEN22, extended + struct.pack('<HH', 14, 0)), key(a), TOKEN22)[0]
    assert vault_check(None, key(a), LEGACY)[0] == ['MISSING_VAULT']
    print('[ORACLE235M_V3_TEST_PASS] pool_layout=TRUE bytearray=TRUE vaults=TRUE token22=TRUE', flush=True)


def run():
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO' or os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_SIGNER_OR_LIVE_ARM_PRESENT')
    url = os.getenv('SOLANA_RPC_URL', '')
    if not url.startswith('https://'):
        raise RuntimeError('HOLD_RPC_MISSING')
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle186_direct_route_truth as d
    old_rpc = r.q87.c.rpc
    report = {'build': 'ORACLE235M_V3', 'signing': False, 'broadcast': False,
              'execution_admission': False, 'pricing_certified': False,
              'mriya_certified': False, 'pairs': [], 'errors': []}
    try:
        r.q87.c.rpc = d.restricted_rpc_factory(old_rpc)
        state, _ = r.q25.prepare_once(Path.cwd())
        r.q25.bind_cached_state(state)
        r.install_proven_hot_math(state)
        pairs = list(state.get('pairs') or [])[:12]
        addresses = sorted({addr for pair in pairs for addr in (
            str(pair.pump_pool), str(pair.pump_base_vault),
            str(pair.pump_quote_vault), str(pair.token), WSOL)})
        slot, data = fetch(addresses, url)
        report['context_slot'] = slot
        report['unique_accounts'] = len(addresses)
        for pair in pairs:
            try:
                report['pairs'].append(check_pair(pair, data))
            except Exception as exc:
                report['pairs'].append({'token': str(pair.token), 'status': 'HOLD',
                                        'reasons': [type(exc).__name__]})
    except Exception as exc:
        report['errors'].append(type(exc).__name__)
    finally:
        r.q87.c.rpc = old_rpc
        report['vault_account_pass'] = sum(x['status'] == 'PASS_POOL_VAULT_ACCOUNT_FIELDS'
                                           for x in report['pairs'])
        report['status'] = 'HOLD_ATOMIC_EXECUTION_SAFETY'
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE235M_RESULT]', json.dumps({
        'pairs': len(report['pairs']), 'vault_account_pass': report['vault_account_pass'],
        'context_slot': report.get('context_slot'), 'errors': report['errors'],
        'signing': False, 'broadcast': False}, sort_keys=True), flush=True)
    for row in report['pairs']:
        print('[ORACLE235M_PAIR]', json.dumps({
            'token': row['token'][:12], 'status': row['status'],
            'pool_checks': row.get('pool_checks'), 'reasons': row['reasons']},
            sort_keys=True), flush=True)
    print('[REPORT]', REPORT, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if not args.test and not args.run:
        parser.error('specify --test or --run')
    if args.test:
        test()
    if args.run:
        run()
