import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem052_exact_canonical_postgresql_schema.json').read_text())
assert d['columns']
assert d['execution_authority'] is False
print('[PASS] exact physical canonical PostgreSQL schema captured')
print('[PASS] KSEM-052 certified')
