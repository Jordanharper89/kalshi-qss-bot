import json
from pathlib import Path
x=json.loads(Path('runtime_state/solana_live_opportunity/slop037_native_cutover.json').read_text())
assert x['state']=='NATIVE_ORACLE_LIVE_BUY_PRESSURE_CUTOVER_CERTIFIED'
assert x['execution_authority'] is False and x['read_only'] is True
print('[SLOP-037]',x)
print('[PASS] production launcher cutover structurally certified')
print('[NEXT] restart normal run_oracle_LIVE.py to physically activate supervised child')
