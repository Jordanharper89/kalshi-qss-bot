import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem055_exact_kalshi_single_market_source_audit.json').read_text())
assert d['count']>0
assert d['execution_authority'] is False
print('[PASS] exact read-only Kalshi single-market candidates inventoried')
print('[PASS] KSEM-055 certified')
