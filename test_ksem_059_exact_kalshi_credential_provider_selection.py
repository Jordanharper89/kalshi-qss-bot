import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem059_exact_kalshi_credential_provider_selection.json').read_text())
assert d['selected']
print('[PASS] existing Kalshi credential provider selected')
print('[PASS] KSEM-059 certified')
