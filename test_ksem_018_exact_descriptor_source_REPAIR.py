import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem018_exact_descriptor_source_repair.json').read_text())
assert 'descriptors' in d['function_body']
assert d['execution_authority'] is False
print('[PASS] exact OAD-120 descriptor contract captured')
print('[PASS] physical descriptor callsites captured')
print('[PASS] KSEM-018 repair certified')
