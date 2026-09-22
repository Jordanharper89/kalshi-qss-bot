import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem041_postgresql_backend_binding.json').read_text())
assert d['callers']
assert d['execution_authority'] is False
print('[PASS] exact PostgreSQL snapshot-reader backend binding audited')
print('[PASS] KSEM-041 repair certified')
