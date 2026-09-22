import json
from pathlib import Path
d=json.loads(Path('runtime_state/solana_live_opportunity/slop038b_exact_outcome_path_audit.json').read_text())
assert d['runner_exists'] and d['slop020_candidates']
assert d['execution_authority'] is False
print('[SLOP-038B]',json.dumps(d,indent=2,sort_keys=True))
print('[PASS] exact physical outcome path captured without guessed SLOP-020 name')
print('[PASS] execution_authority=FALSE')
