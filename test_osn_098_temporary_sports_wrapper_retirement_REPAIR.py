from pathlib import Path
import json
r=Path('.')
d=json.loads((r/'qseries_v2/oracle_source_network/state/osn098_temporary_wrapper_retirement.json').read_text())
assert not (r/'run_oracle_live_WITH_OSN_SPORTS.py').exists()
assert d['active'] is False and d['production_launcher']=='run_oracle_LIVE.py'
assert d['execution_authority'] is False
print('[PASS] temporary sports wrapper retired/absent')
print('[PASS] run_oracle_LIVE.py is sole production launcher')
print('[PASS] OSN-098 repair certified')
