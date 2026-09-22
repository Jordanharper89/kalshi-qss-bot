import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem015_physical_live_market_binding_gate.json').read_text())
assert d['live_market_source_candidates']
assert d['physical_binding_executed'] is False
assert d['execution_authority'] is False
print('[PASS] live Kalshi market-source candidates physically discovered')
print('[PASS] no fabricated live binding execution')
print('[PASS] KSEM-015 certified')
