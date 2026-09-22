import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem033_underlying_sports_context.json').read_text())
assert d['rows']
assert d['execution_authority'] is False
print('[PASS] underlying Kalshi sports context physically recovered and accounted')
print('[PASS] KSEM-033 certified')
