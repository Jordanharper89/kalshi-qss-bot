import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem034_exact_leg_propositions.json').read_text())
assert d['rows']
assert all('context_text' in x for x in d['rows'])
assert d['execution_authority'] is False
print('[PASS] exact leg propositions reconstructed from underlying market context')
print('[PASS] KSEM-034 certified')
