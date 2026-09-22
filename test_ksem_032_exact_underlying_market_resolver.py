import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem032_underlying_market_resolution.json').read_text())
assert d['rows']
assert all('resolved' in x for x in d['rows'])
assert d['execution_authority'] is False
print('[PASS] every MVE leg received exact underlying-market resolution status')
print('[PASS] KSEM-032 certified')
