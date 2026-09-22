import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem013_exact_semantic_role_resolution.json').read_text())
assert set(d['roles'])=={'market_type','entity','decomposition','classification'}
assert d['roles']['decomposition']['callable']=='decompose_mixed_market'
assert d['roles']['classification']['callable']=='classify_isolated_root_cause'
print('[PASS] decomposition and classification exact roles resolved')
print('[PASS] KSEM-013 certified')
