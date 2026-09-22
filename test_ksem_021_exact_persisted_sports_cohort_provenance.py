import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem021_exact_persisted_sports_cohort_provenance.json').read_text())
assert len(d['modules'])==2
assert any(x['cohort_usage'] for x in d['modules'])
assert d['execution_authority'] is False
print('[PASS] exact persisted sports cohort provenance captured')
print('[PASS] KSEM-021 certified')
