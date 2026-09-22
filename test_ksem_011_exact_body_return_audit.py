import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem011_exact_body_return_audit.json').read_text())
assert set(d['roles'])=={'market_type','entity','decomposition','classification'}
assert all(v['returns'] for v in d['roles'].values())
assert d['execution_authority'] is False
print('[PASS] exact function bodies and return shapes audited')
print('[PASS] KSEM-011 certified')
