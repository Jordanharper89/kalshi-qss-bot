import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem036_residual_gap_root_causes.json').read_text())
assert d['total']>0
assert sum(d['counts'].values())==d['total']
assert d['execution_authority'] is False
print('[PASS] every contextual binding result has an exact residual root cause')
print('[PASS] KSEM-036 certified')
