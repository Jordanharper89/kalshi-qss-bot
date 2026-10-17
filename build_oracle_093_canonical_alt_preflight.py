"""ORACLE-093: install offline, read-only ALT coverage preflight.
No changes to alt_manager, scanner, private-key handling, or RPC.
"""
import argparse
import ast
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_093_alt_preflight.py')
SOURCE = '''"""Read-only ALT coverage planner for a saved complete forward route.
This is an estimate, NOT an executable transaction or on-chain ALT.
"""
import argparse
import json
from pathlib import Path

WIRE_LIMIT = 1232
BASELINE_BYTES = 1343  # Prior observed packet; replace using --baseline.

def eligible(ixs, user):
    if not isinstance(ixs, list) or not ixs:
        raise ValueError('FULL_INSTRUCTIONS_REQUIRED')
    programs = {str(ix['programId']) for ix in ixs}
    seen = set()
    result = []
    for ix in ixs:
        if not isinstance(ix, dict) or not isinstance(ix.get('accounts'), list):
            raise ValueError('INVALID_INSTRUCTION_FORMAT')
        for a in ix['accounts']:
            pk = str(a.get('pubkey', ''))
            if not pk or pk == user or pk in programs or a.get('isSigner') or pk in seen:
                continue
            seen.add(pk)
            result.append(pk)
    return result

def plan(doc, baseline):
    if not isinstance(doc, dict):
        raise ValueError('ROUTE_DOCUMENT_NOT_OBJECT')
    user = doc.get('user') or doc.get('payer')
    if not isinstance(user, str) or not user:
        raise ValueError('PUBLIC_PAYER_REQUIRED_IN_JSON')
    candidates = doc.get('candidates')
    if isinstance(candidates, list):
        matched = [x for x in candidates if isinstance(x, dict) and x.get('name') == 'FULL']
        if not matched:
            raise ValueError('FULL_ATOMIC_CANDIDATE_REQUIRED')
        ixs = matched[0].get('instructions')
    else:
        ixs = doc.get('instructions')
    addresses = eligible(ixs, user)
    if not isinstance(baseline, int) or baseline < 66:
        raise ValueError('INVALID_BASELINE_WIRE_BYTES')
    # With one ALT, each moved 32-byte static key becomes a 1-byte
    # index; reserve 35 bytes for table pubkey, shortvec counts, etc.
    # Conservative estimate for ordinary (<128-key) v0 messages only.
    take = min(8, len(addresses))
    savings_estimate = max(0, 31 * take - 35) if take else 0
    required = max(0, baseline - WIRE_LIMIT)
    return {
        'status': 'ESTIMATE_ONLY_NO_ONCHAIN_ALT',
        'baseline_wire_bytes': baseline,
        'max_wire_bytes': WIRE_LIMIT,
        'reduction_required_bytes': required,
        'eligible_count': len(addresses),
        'selected_count': take,
        'selected_addresses': addresses[:take],
        'estimated_byte_savings': savings_estimate,
        'estimated_result_bytes': baseline - savings_estimate,
        'estimated_meets_limit': savings_estimate >= required,
        'real_alt_verified': False,
        'real_compiled_size_verified': False,
        'atomic_simulation_passed': False,
        'authorization_to_create_alt': False,
        'signing': False,
        'broadcast': False,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Local JSON containing public payer and full atomic instruction accounts')
    ap.add_argument('--baseline', type=int, default=BASELINE_BYTES)
    ns = ap.parse_args()
    doc = json.loads(Path(ns.input).read_text(encoding='utf-8'))
    report = plan(doc, ns.baseline)
    print('[ORACLE093_ALT_COVERAGE] ' + json.dumps(report, sort_keys=True))
    print('[BOUNDARY] NO_RPC NO_KEYS NO_SIGNATURE NO_BROADCAST NO_ALT_MUTATION')
    if report['selected_count'] < 4:
        print('[HOLD] TOO_FEW_ELIGIBLE_ACCOUNTS_FOR_CANONICAL_BUILDER')
    elif report['estimated_meets_limit']:
        print('[HOLD] PROMISING_ESTIMATE_NEEDS_REAL_ALT_AND_EXACT_V0_COMPILATION')
    else:
        print('[HOLD] ESTIMATED_ALT_COVERAGE_INSUFFICIENT')

if __name__ == '__main__':
    main()
'''

def test():
    ast.parse(SOURCE)
    ns = {'__name__': '_oracle093_test_'}
    exec(compile(SOURCE, '<oracle093>', 'exec'), ns)
    def ix(n, signer=False):
        return {'programId': 'program1', 'accounts': [{'pubkey': 'account' + str(j), 'isSigner': signer, 'isWritable': True} for j in range(n)]}
    p = ns['plan']({'user': 'payer1', 'instructions': [ix(8)]}, 1343)
    assert p['eligible_count'] == 8 and p['selected_count'] == 8
    assert p['estimated_byte_savings'] == 213 and p['estimated_result_bytes'] == 1130
    assert p['estimated_meets_limit'] and not p['real_compiled_size_verified']
    p = ns['plan']({'user': 'payer1', 'instructions': [ix(4)]}, 1343)
    assert not p['estimated_meets_limit']
    p = ns['plan']({'user': 'payer1', 'instructions': [ix(8, signer=True)]}, 1343)
    assert p['selected_count'] == 0
    p = ns['plan']({'user': 'payer1', 'candidates': [{'name': 'FULL', 'instructions': [ix(6)]}]}, 1343)
    assert p['selected_count'] == 6
    for bad in ({'user': 'payer1'}, {'instructions': [ix(8)]}):
        try:
            ns['plan'](bad, 1343)
        except ValueError:
            pass
        else:
            raise AssertionError('MISSING_INPUT_ACCEPTED')
    print('[PASS] ORACLE093_ELIGIBILITY_SAVINGS_SIGNER_EXCLUSION_AND_FAIL_CLOSED_TESTS')
    print('[BOUNDARY] NO_RPC NO_PRIVATE_KEY NO_SIGNING NO_BROADCAST NO_ALT_MUTATION')

def install():
    test()
    if TARGET.exists():
        if TARGET.read_text(encoding='utf-8') == SOURCE:
            print('[PASS] ORACLE093_ALREADY_INSTALLED')
            return
        raise RuntimeError('ORACLE093_TARGET_EXISTS_DIFFERENT_CONTENT_REFUSING_OVERWRITE')
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(SOURCE, encoding='utf-8')
    ast.parse(TARGET.read_text(encoding='utf-8'))
    print('[PASS] ORACLE093_OFFLINE_ALT_PREFLIGHT_INSTALLED')
    print('[TARGET]', TARGET)
    print('[NEXT] Provide a saved FULL atomic instruction JSON to --input for account coverage estimate')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    args = ap.parse_args()
    test() if args.test else install()
