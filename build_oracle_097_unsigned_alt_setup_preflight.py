"""ORACLE-097: install a public-only unsigned ALT setup preflight.
Does not sign, create, extend, send, or broadcast an ALT.
"""
import ast
import argparse
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_097_unsigned_alt_setup_preflight.py')
SOURCE = r'''"""ORACLE-097: public ALT setup from approved ORACLE-096 plan, unsigned only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.request

PLAN = Path('runtime_state/oracle/solana_atomic_executor/canonical_alt_plan.json')
BUILDER = Path('qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native/build_qarb096_alt_ix.mjs')
OUTPUT = Path('runtime_state/oracle/solana_atomic_executor/canonical_alt_unsigned_setup.json')
ALT_SIZE_LIMIT = 1232


def validate_plan(d):
    if not isinstance(d, dict) or d.get('revision') != 'ORACLE_096_OFFLINE_CANONICAL_ALT_PLAN':
        raise ValueError('ORACLE096_PLAN_REQUIRED')
    if d.get('status') != 'PLAN_ONLY_NO_ALT_EXISTS' or d.get('theoretical_size_gate') != 'MAY_FIT':
        raise ValueError('PLAN_NOT_ELIGIBLE')
    for k in ('private_key_used', 'signing', 'broadcast', 'authority_to_create_alt'):
        if d.get(k) is not False:
            raise ValueError('PLAN_SAFETY_BOUNDARY_' + k)
    payer, addrs = d.get('public_payer'), d.get('selected_addresses')
    if not isinstance(payer, str) or not isinstance(addrs, list) or not (4 <= len(addrs) <= 8):
        raise ValueError('INVALID_PUBLIC_PLAN')
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    def check_pubkey(x):
        if not isinstance(x, str) or not x or len(x) > 44:
            raise ValueError('INVALID_SOLANA_PUBLIC_KEY')
        n = 0
        for char in x:
            if char not in alphabet:
                raise ValueError('INVALID_SOLANA_PUBLIC_KEY')
            n = n * 58 + alphabet.index(char)
        raw = b'\x00' * (len(x) - len(x.lstrip('1'))) + (n.to_bytes((n.bit_length() + 7)//8, 'big') if n else b'')
        if len(raw) != 32:
            raise ValueError('INVALID_SOLANA_PUBLIC_KEY')
        return raw
    pubkeys = [check_pubkey(x) for x in [payer] + addrs]
    if len(set(pubkeys)) != len(pubkeys):
        raise ValueError('DUPLICATE_OR_PAYER_ADDRESS')
    if any(x in set(d.get('invoked_program_ids') or []) for x in addrs):
        raise ValueError('INVOKED_PROGRAM_IN_ALT')
    if d.get('selected_address_count') != len(addrs):
        raise ValueError('PLAN_COUNT_MISMATCH')
    if type(d.get('baseline_wire_bytes')) is not int or type(d.get('theoretical_wire_bytes')) is not int:
        raise ValueError('SIZE_FIELDS_MISSING')
    if d['baseline_wire_bytes'] - d['theoretical_wire_bytes'] != 31 * len(addrs) - 35:
        raise ValueError('SAVINGS_MISMATCH')
    if d['theoretical_wire_bytes'] > ALT_SIZE_LIMIT:
        raise ValueError('ESTIMATE_OVER_LIMIT')
    return payer, addrs


def finalized_slot(rpc_url):
    payload = json.dumps({'jsonrpc': '2.0', 'id': 97, 'method': 'getSlot',
                          'params': [{'commitment': 'finalized'}]}).encode()
    req = urllib.request.Request(rpc_url, data=payload,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as response:
        obj = json.load(response)
    slot = obj.get('result') if isinstance(obj, dict) and 'error' not in obj else None
    if type(slot) is not int or slot <= 0:
        raise RuntimeError('FINALIZED_SLOT_UNAVAILABLE')
    return slot


def build_public_setup(payer, addrs, slot):
    if not BUILDER.is_file():
        raise FileNotFoundError('EXISTING_ALT_BUILDER_MISSING')
    data = json.dumps({'user': payer, 'recentSlot': slot, 'addresses': addrs})
    result = subprocess.run(['node', BUILDER.name], cwd=BUILDER.parent,
                            input=data, text=True, capture_output=True, timeout=20)
    if result.returncode:
        raise RuntimeError('NODE_ALT_BUILDER_FAILED: ' + result.stderr[-300:])
    try:
        row = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as e:
        raise RuntimeError('NODE_ALT_BUILDER_INVALID_OUTPUT') from e
    if not row.get('ok'):
        raise RuntimeError('NODE_ALT_BUILDER_REFUSED: ' + str(row.get('reason'))[:200])
    if row.get('addresses') != addrs or row.get('recentSlot') != slot:
        raise RuntimeError('BUILDER_INPUT_ECHO_MISMATCH')
    if not isinstance(row.get('lookupTable'), str) or len(row.get('instructions') or []) != 2:
        raise RuntimeError('BUILDER_MALFORMED_SETUP')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', default=str(PLAN))
    parser.add_argument('--output', default=str(OUTPUT))
    parser.add_argument('--rpc-url', default=None,
                        help='Optional endpoint without credentials in CMD history; prefer SOLANA_RPC_URL env')
    args = parser.parse_args()
    doc = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    payer, addrs = validate_plan(doc)
    url = args.rpc_url or os.environ.get('SOLANA_RPC_URL') or 'https://api.mainnet-beta.solana.com'
    if not url.startswith('https://'):
        raise ValueError('HTTPS_RPC_REQUIRED')
    slot = finalized_slot(url)
    setup = build_public_setup(payer, addrs, slot)
    out = {'revision': 'ORACLE_097_UNSIGNED_ALT_SETUP',
           'status': 'UNSIGNED_PREPARATION_ONLY', 'public_payer': payer,
           'token': doc['capture_token'], 'lookup_table_address': setup['lookupTable'],
           'recent_finalized_slot': slot, 'addresses': addrs,
           'unsigned_instructions': setup['instructions'],
           'theoretical_wire_bytes': doc['theoretical_wire_bytes'],
           'real_alt_verified': False, 'actual_v0_bytes_verified': False,
           'atomic_simulation_passed': False, 'authorization_to_create_alt': False,
           'private_key_used': False, 'signing': False, 'broadcast': False}
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + '.tmp')
    tmp.write_text(json.dumps(out, indent=2, sort_keys=True), encoding='utf-8')
    tmp.replace(dest)
    print('[ORACLE097_UNSIGNED_ALT_SETUP] ' + json.dumps({
        'table': out['lookup_table_address'], 'addresses': len(addrs),
        'slot': slot, 'instructions': len(out['unsigned_instructions']),
        'theoretical_wire_bytes': out['theoretical_wire_bytes'],
        'signing': False, 'broadcast': False}, sort_keys=True))
    print('[ORACLE097_PLAN_PATH]', dest)
    print('[HOLD] NOT_ONCHAIN_ALT; NO_SIGNED_PACKET; FINALIZED_SLOT_EXPIRES_FOR_CREATION')

if __name__ == '__main__':
    main()
'''


def test():
    ast.parse(SOURCE)
    n = {'__name__': '_test'}
    exec(compile(SOURCE, 'oracle097', 'exec'), n)
    p = 'DshvULBw4foHgiqLksn8H6vHWredDT6mrJBmKLTFJih6'
    addrs = ['8FZiH18SPftb88k8on81jzEQbGBAyztaAKYqT7KH5CAx',
             'So11111111111111111111111111111111111111112',
             '4BEMesYzs2Gucu5m5nQKgoze7pawLYHTWPzReThAdXS6',
             'FQTs7tHw8vM9tUCU6PuRB3r6VK835cvMWZBJBHiBXKoq',
             'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb',
             '2tqyiusynfmwfgFDndWR2FszsCrwMJ4r7GJP9BAXGJxE',
             'ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw',
             '7jehcf8mPFTwwvKVtMZJBjtN3xPf5tiu625GWwGnAKYG']
    d = dict(revision='ORACLE_096_OFFLINE_CANONICAL_ALT_PLAN',
             status='PLAN_ONLY_NO_ALT_EXISTS', theoretical_size_gate='MAY_FIT',
             private_key_used=False, signing=False, broadcast=False,
             authority_to_create_alt=False, public_payer=p, selected_addresses=addrs,
             selected_address_count=8, invoked_program_ids=[], baseline_wire_bytes=1343,
             theoretical_wire_bytes=1130)
    assert n['validate_plan'](d) == (p, addrs)
    for change in ({'signing': True}, {'selected_addresses': [p] + addrs[1:]},
                   {'invoked_program_ids': [addrs[1]]}, {'theoretical_wire_bytes': 1200}):
        bad = {**d, **change}
        try:
            n['validate_plan'](bad)
        except ValueError:
            pass
        else:
            raise AssertionError('UNSAFE_PLAN_ACCEPTED:' + str(change))
    if TARGET.exists():
        ast.parse(TARGET.read_text(encoding='utf-8'))
    print('[PASS] ORACLE097_PUBLIC_PLAN_VALIDATION_AND_FAIL_CLOSED_TESTS')
    print('[BOUNDARY] INSTALL_TEST_NO_RPC_NO_KEYS_NO_SIGNING_NO_BROADCAST_NO_ALT_MUTATION')


def install():
    test()
    if TARGET.exists():
        if TARGET.read_text(encoding='utf-8') != SOURCE:
            raise RuntimeError('ORACLE097_DIFFERENT_EXISTING_TARGET_REFUSE_OVERWRITE')
        print('[PASS] ORACLE097_ALREADY_INSTALLED')
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(SOURCE, encoding='utf-8')
    print('[PASS] ORACLE097_UNSIGNED_ALT_SETUP_PREFLIGHT_INSTALLED')
    print('[TARGET]', TARGET)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()
    test() if args.test else install()
