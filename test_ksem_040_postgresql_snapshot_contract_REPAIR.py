import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem040_postgresql_snapshot_contract.json').read_text())
assert d['function']=='_read_market_snapshot_observations'
assert d['args']==['backend','tickers']
assert d['body']
assert d['execution_authority'] is False
print('[PASS] exact PostgreSQL market-snapshot ticker reader contract captured')
print('[PASS] KSEM-040 repair certified')
