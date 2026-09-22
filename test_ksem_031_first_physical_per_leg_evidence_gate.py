import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem031_first_physical_per_leg_evidence_gate.json').read_text())
assert d['total_legs']>0
assert sum(d['counts'].values())==d['total_legs']
assert all(x['status'] in ('EXACT_BOUND','AMBIGUOUS','SOURCE_GAP') for x in d['results'])
assert d['execution_authority'] is False
print('[PASS] every physical sports leg accounted for without fabricated binding')
print('[PASS] KSEM-031 certified')
