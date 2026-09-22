import json
from pathlib import Path
x=json.loads(Path('runtime_state/solana_live_opportunity/slop033b_native_child_contract.json').read_text())
assert x['children'] and x['has_start'] and x['has_run_forever']
assert x['execution_authority'] is False
print('[SLOP-033B]',x)
print('[PASS] exact production native-child contract captured read-only')
