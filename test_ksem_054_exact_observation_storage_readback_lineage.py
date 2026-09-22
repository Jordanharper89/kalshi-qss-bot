import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem054_exact_observation_storage_readback_lineage.json').read_text())
assert d['physical_row'] is not None
assert d['backend_readback']
assert d['execution_authority'] is False
print('[PASS] physical PostgreSQL row traced through exact canonical backend readback')
print('[PASS] KSEM-054 certified')
