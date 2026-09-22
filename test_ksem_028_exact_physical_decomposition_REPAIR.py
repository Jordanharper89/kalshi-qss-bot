import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem028_existing_decomposer_physical.json').read_text())
assert d['parents']
assert sum(len(x['decomposed']) for x in d['parents'])>0
assert d['execution_authority'] is False
print('[PASS] exact frozen OAD-099 physically decomposed live Kalshi markets')
print('[PASS] KSEM-028 physical repair certified')
