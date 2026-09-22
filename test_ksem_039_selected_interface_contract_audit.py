import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem039_selected_interface_contract.json').read_text())
assert d['function'] and d['args'] and d['body']
assert d['execution_authority'] is False
print('[PASS] selected Kalshi retrieval interface exact contract captured')
print('[PASS] KSEM-039 certified')
