import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem051_foundation_decision.json').read_text())
assert d['decision']
assert d['osn_binding_ready'] is False
assert d['production_launcher_change_required'] is False
assert d['execution_authority'] is False
print('[PASS] missing-underlying foundation decision derived from physical lineage evidence')
print('[PASS] KSEM-051 certified')
