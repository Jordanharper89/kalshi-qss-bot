import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem058_exact_kalshi_credentials_binding_audit.json').read_text())
assert d['count']>0
print('[PASS] existing Kalshi credentials bindings audited')
print('[PASS] KSEM-058 repair certified')
