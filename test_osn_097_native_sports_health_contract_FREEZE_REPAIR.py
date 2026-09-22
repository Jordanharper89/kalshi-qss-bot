import json
from pathlib import Path
d=json.loads(Path('qseries_v2/oracle_source_network/state/osn097_native_sports_health_contract.json').read_text())
assert d['six_league_full_cycle_certified'] is True
assert d['sports_heartbeat_advanced'] is True
assert d['restart_recovery_physical_certified'] is False
assert d['restart_recovery_status']=='DEFERRED_TO_ORACLE_RUNTIME_HARDENING'
assert d['execution_authority'] is False
print('[PASS] native sports HEALTHY contract frozen from OSN-095 physical proof')
print('[PASS] restart recovery explicitly not overclaimed')
print('[PASS] OSN-097 freeze repair certified')
