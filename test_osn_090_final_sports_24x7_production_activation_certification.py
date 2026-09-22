from pathlib import Path
import json
from qseries_v2.oracle_source_network.certification.final_sports_24x7_activation import certify
r=certify(Path.cwd()); print('[FINAL]',r)
assert r['activation_ready'] is True
assert r['base_launcher_unchanged'] is True
assert r['bounded_dual_runtime_certified'] is True
assert r['execution_authority'] is False
p=Path.cwd()/'qseries_v2/oracle_source_network/state/osn090_final_sports_24x7_activation.json'
p.write_text(json.dumps(r,indent=2),encoding='utf-8')
print('[STATE]',p)
print('[PASS] sports 24x7 production activation path certified')
print('[PASS] use run_oracle_live_WITH_OSN_SPORTS.py for combined Oracle + sports runtime')
print('[PASS] execution_authority=FALSE')
