"""ORACLE-095: complete offline strict ALT-coverage installer. No network/wallet."""
import argparse
import ast
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_095_strict_alt_coverage.py')
SOURCE = r'''"""Strict, read-only ALT projection against ORACLE-094 public account capture."""
import argparse
import json
from pathlib import Path

LIMIT = 1232

def analyze(doc, baseline):
    if type(baseline) is not int or baseline < 66:
        raise ValueError('INVALID_BASELINE')
    if doc.get('capture_scope') != 'PUBLIC_ACCOUNT_KEYS_ONLY' or doc.get('data_included') is not False:
        raise ValueError('EXPECTED_ORACLE094_PUBLIC_CAPTURE')
    user = doc.get('user')
    if not isinstance(user, str) or not user:
        raise ValueError('PUBLIC_PAYER_MISSING')
    full = [c for c in doc.get('candidates', []) if isinstance(c, dict) and c.get('name') == 'FULL']
    if len(full) != 1 or not isinstance(full[0].get('instructions'), list) or not full[0]['instructions']:
        raise ValueError('ONE_FULL_ROUTE_REQUIRED')
    ixs = full[0]['instructions']
    programs = set()
    signers = {user}
    for ix in ixs:
        if not isinstance(ix, dict) or not isinstance(ix.get('programId'), str) or not isinstance(ix.get('accounts'), list):
            raise ValueError('INVALID_INSTRUCTION')
        programs.add(ix['programId'])
        for a in ix['accounts']:
            if not isinstance(a, dict) or not isinstance(a.get('pubkey'), str) or not isinstance(a.get('isSigner'), bool):
                raise ValueError('INVALID_ACCOUNT')
            if a['isSigner']:
                signers.add(a['pubkey'])
    selected = []
    seen = set()
    for ix in ixs:
        for a in ix['accounts']:
            key = a['pubkey']
            if key not in seen:
                seen.add(key)
                if key not in programs and key not in signers:
                    selected.append(key)
    top = selected[:8]
    # Estimate, NOT measured. Solana v0 static key -> ALT index generally saves ~31 bytes
    # minus one table key and its index/count overhead. No live table is implied.
    estimated_savings = max(0, len(top) * 31 - 35) if top else 0
    required = max(0, baseline - LIMIT)
    return dict(status='ESTIMATE_ONLY_STRICT_ELIGIBILITY', token=doc.get('token'),
        baseline_wire_bytes=baseline, max_wire_bytes=LIMIT, required_savings=required,
        instruction_count=len(ixs), unique_program_ids=len(programs), unique_signers=len(signers),
        eligible_account_count=len(selected), selected_count=len(top), selected_addresses=top,
        estimated_savings=estimated_savings, estimated_wire_bytes=baseline-estimated_savings,
        estimated_meets_limit=estimated_savings>=required,
        onchain_alt_verified=False, exact_v0_compilation_verified=False,
        atomic_simulation_passed=False, signing=False, broadcast=False)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--baseline', type=int, required=True)
    args = p.parse_args()
    doc = json.loads(Path(args.input).read_text(encoding='utf-8'))
    result = analyze(doc, args.baseline)
    print('[ORACLE095_STRICT_ALT_COVERAGE] ' + json.dumps(result, sort_keys=True))
    print('[BOUNDARY] OFFLINE_NO_RPC_NO_PRIVATE_KEY_NO_SIGNING_NO_BROADCAST_NO_ALT_MUTATION')
    print('[HOLD] ESTIMATE_NOT_AN_ONCHAIN_ALT_OR_EXECUTABLE_TRANSACTION')

if __name__ == '__main__':
    main()
'''

def test():
    ns = {'__name__': '_oracle095_tests'}
    exec(compile(SOURCE, '<oracle095>', 'exec'), ns)
    pk = lambda n: f'pk{n:032d}'
    program, payer, token_program = pk(1), pk(2), pk(3)
    ix = {'programId': program, 'accounts': [
        {'pubkey': payer, 'isSigner': True},
        {'pubkey': token_program, 'isSigner': False},
        *[{'pubkey': pk(i), 'isSigner': False} for i in range(4, 13)] ]}
    doc = {'capture_scope': 'PUBLIC_ACCOUNT_KEYS_ONLY', 'data_included': False,
           'user': payer, 'token': 'T', 'candidates': [{'name': 'FULL', 'instructions':
           [ix, {'programId': token_program, 'accounts': ix['accounts']}]}]}
    result = ns['analyze'](doc, 1343)
    assert result['selected_count'] == 8 and result['estimated_savings'] == 213
    assert token_program not in result['selected_addresses']
    assert payer not in result['selected_addresses']
    assert result['estimated_meets_limit'] and not result['exact_v0_compilation_verified']
    try:
        ns['analyze']({**doc, 'data_included': True}, 1343)
    except ValueError:
        pass
    else:
        raise AssertionError('UNSAFE_CAPTURE_ADMITTED')
    assert ast.parse(SOURCE)
    print('[PASS] ORACLE095_STRICT_PROGRAM_SIGNER_EXCLUSION_AND_FAIL_CLOSED_TESTS')
    print('[BOUNDARY] NO_RPC NO_KEYS NO_SIGNING NO_BROADCAST NO_SCANNER_EDIT')

def install():
    test()
    if TARGET.exists():
        if TARGET.read_text(encoding='utf-8') != SOURCE:
            raise RuntimeError('TARGET_EXISTS_DIFFERENT_REFUSING_OVERWRITE')
        print('[PASS] ORACLE095_ALREADY_INSTALLED')
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(SOURCE, encoding='utf-8')
    print('[PASS] ORACLE095_STRICT_ALT_COVERAGE_INSTALLED')
    print('[TARGET]', TARGET)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    test() if args.test else install()
