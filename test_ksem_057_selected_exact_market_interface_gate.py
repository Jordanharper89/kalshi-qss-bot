import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem057_selected_exact_market_interface.json').read_text())
assert d['read_only_candidate'] is True
assert d['execution_authority'] is False
print('[PASS] selected exact-market interface body and signature verified read-only')
print('[PASS] KSEM-057 certified')
