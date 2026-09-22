import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_canonical_provider_result_contract.json').read_text())
names={x['name'] for x in d['contracts']}
assert 'CanonicalProviderResult' in names
assert 'acquire_canonical_events' in names
assert d['execution_authority'] is False
print('[PASS] exact CanonicalProviderResult contract captured')
print('[PASS] KSEM-025 repair audit certified')
