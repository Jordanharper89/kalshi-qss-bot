"""MTR-154: public read-only Solana ALT account evidence.
No signing, no wallet operations, no swap construction.
"""
import argparse
import base64
import hashlib
import json
import struct
import urllib.request
from types import MappingProxyType
from .mtr_152_native_envelope_inspector import _base58
from .mtr_153_v0_alt_account_resolver import _parse_v0, resolve_v0

ALT_OWNER = 'AddressLookupTab1e1111111111111111111111111'
MAX_U64 = (1 << 64) - 1

class ALTProofError(ValueError):
    pass

def base58_decode(s):
    if not isinstance(s, str) or not s:
        raise ALTProofError('BAD_ADDRESS')
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    n = 0
    for ch in s:
        if ch not in alphabet:
            raise ALTProofError('BAD_ADDRESS')
        n = n * 58 + alphabet.index(ch)
    b = n.to_bytes((n.bit_length() + 7) // 8, 'big') if n else b''
    out = b'\0' * (len(s) - len(s.lstrip('1'))) + b
    if len(out) != 32 or _base58(out) != s:
        raise ALTProofError('NONCANONICAL_ADDRESS')
    return out

def decode_table(table, result, min_slot=0):
    """Require RPC-shaped getAccountInfo context, ALT owner and valid account state.
    Proof is conditional on the selected RPC's trustworthiness and freshness.
    """
    base58_decode(table)
    if not isinstance(result, dict):
        raise ALTProofError('RPC_SHAPE')
    context = result.get('context')
    account = result.get('value')
    if not isinstance(context, dict) or not isinstance(account, dict):
        raise ALTProofError('ACCOUNT_MISSING')
    slot = context.get('slot')
    if type(slot) is not int or slot < min_slot:
        raise ALTProofError('RPC_SLOT_TOO_OLD')
    if account.get('owner') != ALT_OWNER or account.get('executable') is not False:
        raise ALTProofError('WRONG_OWNER_OR_EXECUTABLE')
    if type(account.get('lamports')) is not int or account['lamports'] <= 0:
        raise ALTProofError('UNFUNDED_ACCOUNT')
    data = account.get('data')
    if not isinstance(data, list) or len(data) != 2 or data[1] != 'base64':
        raise ALTProofError('ACCOUNT_ENCODING')
    try:
        raw = base64.b64decode(data[0], validate=True)
    except Exception as exc:
        raise ALTProofError('INVALID_BASE64') from exc
    if len(raw) < 56 or (len(raw) - 56) % 32 or (len(raw)-56)//32 > 256:
        raise ALTProofError('INVALID_ALT_LENGTH')
    if struct.unpack_from('<I', raw, 0)[0] != 1:
        raise ALTProofError('INVALID_ALT_STATE')
    deactivated = struct.unpack_from('<Q', raw, 4)[0]
    if deactivated != MAX_U64:
        raise ALTProofError('DEACTIVATING_TABLE_HOLD')
    # Last-extended slot and start-index fields are part of the 56-byte metadata.
    last_extended = struct.unpack_from('<Q', raw, 12)[0]
    start_index = raw[20]
    authority_option = raw[21]
    if authority_option not in (0, 1) or last_extended > slot:
        raise ALTProofError('INVALID_META')
    n = (len(raw) - 56)//32
    if start_index > n:
        raise ALTProofError('INVALID_EXTENSION_INDEX')
    addresses = tuple(raw[i:i+32] for i in range(56, len(raw), 32))
    if not addresses:
        raise ALTProofError('EMPTY_ALT')
    return MappingProxyType({
        'table': table, 'rpc_slot': slot, 'addresses': addresses,
        'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'last_extended_slot': last_extended,
        'last_extended_slot_start_index': start_index,
        'account_count': len(addresses),
        'owner_checked': True, 'active_at_rpc_slot': True,
        'signing_authorized': False, 'broadcast_authorized': False
    })

def rpc_table(rpc_url, table, min_slot=0, timeout=10):
    if not isinstance(rpc_url, str) or not rpc_url.startswith('https://'):
        raise ALTProofError('HTTPS_RPC_REQUIRED')
    base58_decode(table)
    request = {
        'jsonrpc': '2.0', 'id': 154, 'method': 'getAccountInfo',
        'params': [table, {'encoding': 'base64', 'commitment': 'finalized',
                           'minContextSlot': min_slot}]
    }
    req = urllib.request.Request(rpc_url, json.dumps(request).encode(),
                                 headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = json.loads(response.read(750000))
    if not isinstance(body, dict) or body.get('error') or body.get('id') != 154:
        raise ALTProofError('RPC_ERROR')
    return decode_table(table, body.get('result'), min_slot)

def verify_transaction_tables(raw, read_table):
    """Fetch exactly the v0 transaction's referenced tables; reject absent indexes.
    Caller supplies a trusted read_table(table) callback; never hydrate on HOT path.
    """
    _, _, refs = _parse_v0(raw)
    if not refs:
        raise ALTProofError('TRANSACTION_HAS_NO_LOOKUPS')
    tables, proofs = {}, []
    for key, writable, readonly in refs:
        if key in tables:
            raise ALTProofError('DUPLICATE_TABLE')
        proof = read_table(key)
        if proof['table'] != key or not proof['owner_checked'] or not proof['active_at_rpc_slot']:
            raise ALTProofError('TABLE_PROOF_MISMATCH')
        seq = proof['addresses']
        if any(idx >= len(seq) for idx in writable + readonly):
            raise ALTProofError('LOOKUP_INDEX_OUT_OF_RANGE')
        tables[key] = seq
        proofs.append(proof)
    resolved = resolve_v0(raw, tables)
    return MappingProxyType({
        'resolved': resolved, 'rpc_proofs': tuple(proofs),
        'rpc_table_evidence_available': True,
        'authenticity_absolute': False,
        'atomic_two_leg_proven': False,
        'protected_profit_certified': False,
        'signing_authorized': False, 'broadcast_authorized': False
    })

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--rpc', default=None)
    parser.add_argument('--table', default=None)
    args = parser.parse_args(argv)
    if bool(args.rpc) != bool(args.table):
        parser.error('--rpc and --table must be provided together')
    if args.rpc:
        proof = rpc_table(args.rpc, args.table)
        print('[MTR154_RPC_ALT] ACCOUNT_VALIDATED')
        print('[MTR154_TABLE]', proof['table'])
        print('[MTR154_SLOT]', proof['rpc_slot'])
        print('[MTR154_ADDRESSES]', proof['account_count'])
        print('[MTR154_HASH]', proof['raw_sha256'])
    else:
        print('[MTR154] READ_ONLY_ALT_PROOF_READER_READY')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[ATOMIC_TWO_LEG_PROOF] FALSE')
    print('[PROTECTED_PROFIT] FALSE')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')

if __name__ == '__main__':
    main()
