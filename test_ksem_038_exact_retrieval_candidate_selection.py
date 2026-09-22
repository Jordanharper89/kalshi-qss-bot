import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem038_exact_retrieval_candidate_selection.json').read_text())
assert d['viable'] and d['selected']['score']>=100
assert d['execution_authority'] is False
print('[PASS] exact identifier-capable Kalshi retrieval candidate selected from physical audit')
print('[PASS] KSEM-038 certified')
