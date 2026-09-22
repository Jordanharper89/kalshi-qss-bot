import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem010_exact_live_binding_execution_readiness.json').read_text())
assert d['canonical_binding_contract_ready'] and d['binding_lineage_ready']
assert d['live_market_binding_executed'] is False
assert d['execution_authority'] is False
print('[PASS] live binding readiness truthfully classified')
print('[PASS] no fake live Kalshi-to-event binding claimed')
print('[PASS] KSEM-010 certified')
