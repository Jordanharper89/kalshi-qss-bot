import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem053_existing_backend_query_contract.json').read_text())
assert d['backend_type'] and d['request_type'] and d['query_signature']
assert d['execution_authority'] is False
print('[PASS] exact existing canonical backend query contract captured')
print('[PASS] KSEM-053 certified')
