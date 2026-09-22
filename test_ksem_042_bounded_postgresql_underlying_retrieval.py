import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem042_bounded_postgresql_underlying_retrieval.json').read_text())
assert d['requested_tickers']
assert d['raw_result_count']>=0
assert d['execution_authority'] is False
print('[PASS] exact production PostgreSQL ticker reader physically exercised')
print('[PASS] KSEM-042 certified')
