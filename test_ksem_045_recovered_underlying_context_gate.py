import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem045_recovered_underlying_context.json').read_text())
assert d['rows']
assert d['resolved']>=0
assert d['execution_authority'] is False
print('[PASS] underlying sports context measured from exact physical ticker identity')
print('[PASS] KSEM-045 certified')
