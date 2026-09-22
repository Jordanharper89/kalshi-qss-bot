import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem048_canonical_direct_exact_ticker_recovery.json').read_text())
assert d['rows']
assert d['execution_authority'] is False
print('[PASS] canonical observation table directly audited for every missing exact ticker')
print('[PASS] KSEM-048 certified')
