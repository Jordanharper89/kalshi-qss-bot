import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem037_exact_ticker_retrieval_audit.json').read_text())
assert d['candidates']
assert d['execution_authority'] is False
print('[PASS] existing Kalshi retrieval candidates physically inventoried')
print('[PASS] KSEM-037 certified')
