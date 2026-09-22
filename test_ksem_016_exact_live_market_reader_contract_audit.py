import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem016_live_market_reader_contract.json').read_text())
assert set(d['targets'])=={'oiar_047','oad_120'}
assert d['execution_authority'] is False
print('[PASS] exact live market and sports-candidate contracts audited')
print('[PASS] KSEM-016 certified')
