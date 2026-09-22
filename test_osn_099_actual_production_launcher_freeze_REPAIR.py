from pathlib import Path
import json,hashlib
r=Path('.')
d=json.loads((r/'qseries_v2/oracle_source_network/state/osn099_actual_production_launcher_freeze.json').read_text())
assert hashlib.sha256((r/'run_oracle_LIVE.py').read_bytes()).hexdigest()==d['sha256']
assert d['sports_native_child'] and d['six_league_physical_cycle_certified']
assert d['restart_recovery_physical_certified'] is False
assert d['temporary_wrapper_retired'] and d['execution_authority'] is False
print('[PASS] exact run_oracle_LIVE.py hash frozen')
print('[PASS] restart recovery not falsely certified')
print('[PASS] OSN-099 repair certified')
