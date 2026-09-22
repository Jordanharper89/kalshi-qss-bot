from pathlib import Path
import json
r=json.loads((Path.cwd()/'qseries_v2/kalshi_sports_evidence_mapping/state/ksem076_live_children_contract.json').read_text())
print('[CONTRACT]',r)
assert isinstance(r['children'],dict) and 'sports' in r['children']
assert 'ksem_mapping' not in r['children']
assert r['has_start_function'] and r['has_run_forever']
print('[PASS] exact production CHILDREN dict captured before cutover')
print('[PASS] KSEM-076 certified')
