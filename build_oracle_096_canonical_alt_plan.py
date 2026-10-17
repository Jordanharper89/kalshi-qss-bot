"""ORACLE-096 full offline canonical ALT plan installer.
No private keys, network, transaction creation, signing, or broadcast.
"""
import argparse
import ast
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_096_canonical_alt_plan.py')
SOURCE = r'''"""ORACLE-096: offline canonical ALT coverage plan for public ORACLE-094 capture."""
import argparse
import json
from pathlib import Path

WIRE_LIMIT = 1232
MAX_ADDRESSES = 8


def plan(doc, baseline):
    if type(baseline) is not int or not (66 <= baseline <= 10000):
        raise ValueError('INVALID_BASELINE')
    if not isinstance(doc, dict) or doc.get('capture_scope') != 'PUBLIC_ACCOUNT_KEYS_ONLY' or doc.get('data_included') is not False:
        raise ValueError('ORACLE094_PUBLIC_CAPTURE_REQUIRED')
    user = doc.get('user')
    token = doc.get('token')
    if not isinstance(user, str) or not (32 <= len(user) <= 44):
        raise ValueError('PUBLIC_PAYER_REQUIRED')
    if not isinstance(token, str) or not (32 <= len(token) <= 44):
        raise ValueError('TOKEN_REQUIRED')
    rows = [c for c in doc.get('candidates', []) if isinstance(c, dict) and c.get('name') == 'FULL']
    if len(rows) != 1 or not isinstance(rows[0].get('instructions'), list) or not rows[0]['instructions']:
        raise ValueError('EXACTLY_ONE_FULL_CANDIDATE_REQUIRED')
    ixs = rows[0]['instructions']
    if len(ixs) > 64:
        raise ValueError('TOO_MANY_INSTRUCTIONS')
    programs, signers, seen, eligible = set(), {user}, set(), []
    for ix in ixs:
        if not isinstance(ix, dict) or not isinstance(ix.get('programId'), str) or not isinstance(ix.get('accounts'), list):
            raise ValueError('INVALID_INSTRUCTION')
        if not (32 <= len(ix['programId']) <= 44) or len(ix['accounts']) > 128:
            raise ValueError('INVALID_INSTRUCTION_SHAPE')
        programs.add(ix['programId'])
        for a in ix['accounts']:
            if not isinstance(a, dict) or not isinstance(a.get('pubkey'), str) or type(a.get('isSigner')) is not bool or type(a.get('isWritable')) is not bool:
                raise ValueError('INVALID_ACCOUNT')
            k = a['pubkey']
            if not (32 <= len(k) <= 44):
                raise ValueError('INVALID_PUBLIC_KEY_LENGTH')
            if a['isSigner']:
                signers.add(k)
    for ix in ixs:
        for a in ix['accounts']:
            k = a['pubkey']
            if k not in seen:
                seen.add(k)
                if k not in signers and k not in programs:
                    eligible.append(k)
    selected = eligible[:MAX_ADDRESSES]
    if len(set(selected)) != len(selected) or any(k in programs or k in signers for k in selected):
        raise AssertionError('INELIGIBLE_LOOKUP_ENTRY')
    savings = max(0, 31 * len(selected) - 35) if selected else 0
    required = max(0, baseline - WIRE_LIMIT)
    return {
        'revision': 'ORACLE_096_OFFLINE_CANONICAL_ALT_PLAN', 'status': 'PLAN_ONLY_NO_ALT_EXISTS',
        'capture_token': token, 'public_payer': user, 'candidate': 'FULL',
        'instruction_count': len(ixs), 'eligible_accounts': len(eligible),
        'invoked_program_ids': sorted(programs), 'signer_count': len(signers),
        'selected_address_count': len(selected), 'selected_addresses': selected,
        'existing_builder_supported': 4 <= len(selected) <= 8,
        'baseline_wire_bytes': baseline, 'wire_limit': WIRE_LIMIT,
        'required_savings': required, 'theoretical_savings': savings,
        'theoretical_wire_bytes': baseline-savings,
        'theoretical_size_gate': 'MAY_FIT' if savings >= required else 'INSUFFICIENT',
        'real_alt_verified': False, 'actual_v0_bytes_verified': False,
        'atomic_simulation_passed': False, 'private_key_used': False,
        'signing': False, 'broadcast': False, 'authority_to_create_alt': False,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--baseline', type=int, required=True)
    ap.add_argument('--output', default='runtime_state/oracle/solana_atomic_executor/canonical_alt_plan.json')
    args = ap.parse_args()
    doc = json.loads(Path(args.input).read_text(encoding='utf-8'))
    out = plan(doc, args.baseline)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix+'.tmp')
    tmp.write_text(json.dumps(out, sort_keys=True, indent=2), encoding='utf-8')
    tmp.replace(dest)
    print('[ORACLE096_ALT_PLAN] '+json.dumps({k:out[k] for k in (
        'capture_token','eligible_accounts','selected_address_count','required_savings',
        'theoretical_savings','theoretical_wire_bytes','theoretical_size_gate',
        'real_alt_verified','actual_v0_bytes_verified','signing','broadcast')}, sort_keys=True))
    print('[ORACLE096_PLAN_PATH]', dest)
    print('[HOLD] PLAN_ONLY_NOT_AN_ONCHAIN_ALT_NOT_AN_EXECUTABLE_PACKET')

if __name__ == '__main__':
    main()
'''


def test():
    ast.parse(SOURCE)
    ns = {'__name__': '_oracle096_testing'}
    exec(compile(SOURCE, '<oracle096>', 'exec'), ns)
    pk = lambda i: ('A' * 29 + f'{i:03d}')
    payer, program, token_program = pk(1), pk(2), pk(3)
    accounts = [{'pubkey': payer, 'isSigner': True, 'isWritable': True}]
    accounts += [{'pubkey': pk(i), 'isSigner': False, 'isWritable': bool(i%2)} for i in range(4, 16)]
    accounts += [{'pubkey': token_program, 'isSigner': False, 'isWritable': False}]
    doc = {'capture_scope': 'PUBLIC_ACCOUNT_KEYS_ONLY', 'data_included': False,
           'user': payer, 'token': pk(99), 'candidates': [{'name': 'FULL', 'instructions': [
               {'programId': program, 'accounts': accounts},
               {'programId': token_program, 'accounts': accounts}]}]}
    result = ns['plan'](doc, 1343)
    assert result['selected_address_count'] == 8
    assert token_program not in result['selected_addresses']
    assert payer not in result['selected_addresses']
    assert result['theoretical_savings'] == 213 and result['theoretical_wire_bytes'] == 1130
    assert result['theoretical_size_gate'] == 'MAY_FIT'
    assert result['real_alt_verified'] is False and result['signing'] is False
    for bad in ({**doc, 'data_included': True}, {**doc, 'user': 'short'}):
        try:
            ns['plan'](bad, 1343)
        except ValueError:
            pass
        else:
            raise AssertionError('INVALID_CAPTURE_ACCEPTED')
    if TARGET.exists():
        ast.parse(TARGET.read_text(encoding='utf-8'))
    print('[PASS] ORACLE096_PUBLIC_CAPTURE_ALT_PLAN_TESTS')
    print('[BOUNDARY] NO_RPC_NO_PRIVATE_KEY_NO_SIGNING_NO_BROADCAST_NO_ALT_MUTATION')


def install():
    test()
    if TARGET.exists():
        if TARGET.read_text(encoding='utf-8') != SOURCE:
            raise RuntimeError('ORACLE096_DIFFERENT_TARGET_REFUSE_OVERWRITE')
        print('[PASS] ORACLE096_ALREADY_INSTALLED')
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(SOURCE, encoding='utf-8')
    print('[PASS] ORACLE096_CANONICAL_ALT_PLAN_INSTALLED')
    print('[TARGET]', TARGET)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    test() if args.test else install()
