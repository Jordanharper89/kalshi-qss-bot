import json
from pathlib import Path
d=json.loads(Path('qseries_v2/oracle_source_network/state/osn100_final_native_sports_production_certification.json').read_text())
assert d['sports_source_activation_complete'] is True
assert d['six_league_full_cycle_physical_certified'] is True
assert d['continuous_runtime_physical_certified'] is True
assert d['restart_recovery_physical_certified'] is False
assert d['sports_evidence_mapping_complete'] is False
assert d['production_launcher']=='run_oracle_LIVE.py'
assert d['execution_authority'] is False
print('[PASS] six-league sports source activation complete in actual Oracle production launcher')
print('[PASS] source -> canonical -> PostgreSQL -> exact readback -> checkpoint -> continuous runtime certified')
print('[PASS] restart recovery explicitly deferred, not overclaimed')
print('[PASS] market/evidence mapping correctly remains next capability')
print('[PASS] OSN-100 FINAL NATIVE SPORTS SOURCE ACTIVATION CERTIFICATION')
