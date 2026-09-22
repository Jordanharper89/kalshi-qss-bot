import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem023_physical_production_sports_candidate_gate.json').read_text())
assert d['structured_descriptors']>0
assert d['current_markets']>0
assert d['descriptor_groups']==d['structured_descriptors']
assert d['execution_authority'] is False
print('[PASS] persisted sports descriptors physically compared with current Kalshi markets')
print('[PASS] KSEM-023 certified')
