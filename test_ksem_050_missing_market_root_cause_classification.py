import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem050_missing_market_root_causes.json').read_text())
assert d['rows']
assert sum(d['counts'].values())==len(d['rows'])
assert all(x['root_cause'] for x in d['rows'])
assert d['execution_authority'] is False
print('[PASS] every missing exact underlying ticker has one explicit root cause')
print('[PASS] KSEM-050 certified')
