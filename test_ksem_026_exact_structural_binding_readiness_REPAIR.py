import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem026_exact_structural_binding_readiness_repair.json').read_text())
assert d['structural_contracts_ready'] is True
assert d['execution_authority'] is False
print('[PASS] Kalshi descriptor/market and OSN event structural contracts ready')
print('[PASS] KSEM-026 repair certified')
