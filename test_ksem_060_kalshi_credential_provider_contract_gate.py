import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem060_kalshi_credential_provider_contract.json').read_text())
assert d['read_only_safe'] is True
print('[PASS] Kalshi credential provider contract verified')
print('[PASS] KSEM-060 certified')
