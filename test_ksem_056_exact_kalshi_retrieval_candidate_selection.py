import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem056_exact_kalshi_retrieval_candidate_selection.json').read_text())
assert d['selected'] is not None
assert d['selected']['score']>=100
print('[PASS] exact single-market retrieval candidate selected from source')
print('[PASS] KSEM-056 certified')
