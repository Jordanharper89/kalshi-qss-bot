import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem046_underlying_retrieval_readiness.json').read_text())
assert d['sample_size']>0
assert d['resolved']+d['not_found']==d['sample_size']
assert d['decision']
assert d['execution_authority'] is False
print('[PASS] underlying-market retrieval readiness classified from physical evidence')
print('[PASS] KSEM-046 certified')
