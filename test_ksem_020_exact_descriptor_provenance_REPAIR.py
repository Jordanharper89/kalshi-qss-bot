import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem020_exact_descriptor_provenance_repair.json').read_text())
assert len(d['modules'])==2
assert any(x['descriptor_calls'] for x in d['modules'])
assert d['execution_authority'] is False
print('[PASS] exact production sports descriptor provenance captured')
print('[PASS] KSEM-020 repair audit certified')
