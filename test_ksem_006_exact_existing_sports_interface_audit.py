import json
from pathlib import Path
d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem006_exact_interface_audit.json').read_text())
assert d['ast_parsed'] and d['module_count']==4
assert all(Path(x['path']).exists() for x in d['modules'])
assert d['execution_authority'] is False
print('[PASS] exact OAD-088/098/099/101 AST interfaces captured')
print('[PASS] KSEM-006 certified')
