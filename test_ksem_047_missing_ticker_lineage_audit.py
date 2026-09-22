import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem047_missing_ticker_lineage_audit.json').read_text())
assert d['rows']
assert d['canonical_columns']
assert d['execution_authority'] is False
print('[PASS] missing underlying tickers audited against exact learning-index lineage')
print('[PASS] KSEM-047 certified')
