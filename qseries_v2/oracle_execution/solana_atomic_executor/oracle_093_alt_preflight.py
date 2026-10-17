"""Read-only ALT coverage planner for a saved complete forward route.
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
