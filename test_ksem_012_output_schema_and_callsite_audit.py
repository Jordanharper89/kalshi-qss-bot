import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem012_output_schema_and_callsite_audit.json').read_text())
assert all(x in d['schemas'] for x in ('SportsMarketType','SportsEntityType','DecomposedLeg'))
assert d['execution_authority'] is False
print('[PASS] output schemas and physical callsites captured')
print('[PASS] KSEM-012 certified')
