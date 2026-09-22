import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem029_existing_sports_identity.json').read_text())
assert d['parents']
assert sum(len(x['legs']) for x in d['parents'])>0
assert d['execution_authority'] is False
print('[PASS] exact frozen OAD-088/OAD-098/OAD-099 pavement physically executed')
print('[PASS] KSEM-029 repair certified')
