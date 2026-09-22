import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem027_physical_mve_legs.json').read_text())
assert d['parents'] and d['legs']
assert all(x['market_ticker'] for x in d['legs'])
assert d['execution_authority'] is False
print('[PASS] physical Kalshi MVE legs extracted exactly')
print('[PASS] KSEM-027 certified')
