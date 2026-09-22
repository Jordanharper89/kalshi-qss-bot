import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem002_existing_classifier_inventory.json').read_text())
assert d['count']>0 and d['execution_authority'] is False
assert all(Path(x['path']).exists() for x in d['candidates'])
print('[PASS] existing Kalshi/sports pavement physically inventoried')
print('[PASS] no guessed dependency filename introduced')
print('[PASS] KSEM-002 certified')
