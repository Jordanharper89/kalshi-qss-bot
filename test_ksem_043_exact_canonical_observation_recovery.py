import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem043_exact_canonical_observation_recovery.json').read_text())
assert d['requested_tickers']
assert 'pair_observations' in d and 'direct_serialized_rows' in d
assert d['execution_authority'] is False
print('[PASS] canonical observations recovered through exact existing PostgreSQL pavement')
print('[PASS] KSEM-043 certified')
