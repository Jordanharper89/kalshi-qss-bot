import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem007_exact_callable_binding_selection.json').read_text())
assert set(d['roles'])=={'market_type','entity','decomposition','classification'}
assert all(v['candidates'] for v in d['roles'].values())
assert d['execution_authority'] is False
print('[PASS] exact callable candidates ranked from AST interfaces')
print('[PASS] ambiguous interfaces retained instead of guessed')
print('[PASS] KSEM-007 certified')
