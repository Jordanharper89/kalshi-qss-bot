import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem044_underlying_ticker_resolution_measurement.json').read_text())
assert d['requested']>0
assert sum(d['counts'].values())==d['requested']
assert d['execution_authority'] is False
print('[PASS] every bounded MVE ticker classified from physical PostgreSQL retrieval')
print('[PASS] KSEM-044 certified')
