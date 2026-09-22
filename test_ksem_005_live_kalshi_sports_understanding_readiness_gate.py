import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem005_live_understanding_readiness.json').read_text())
assert d['foundation_ready'] and d['physical_repo_candidates']
assert d['live_market_execution_performed'] is False
assert d['silent_guessing_allowed'] is False and d['execution_authority'] is False
print('[PASS] KSEM-001 through KSEM-004 foundation ready')
print('[PASS] exact repo candidates retained for next live binding')
print('[PASS] no fake live-market execution claimed')
print('[PASS] KSEM-005 certified')
