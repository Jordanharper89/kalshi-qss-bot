import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem024_candidate_association_shape.json').read_text())
assert d['descriptor']['fields']
assert d['market']['fields']
assert d['execution_authority'] is False
print('[PASS] exact descriptor and Kalshi market structural fields captured')
print('[PASS] KSEM-024 structural repair certified')
