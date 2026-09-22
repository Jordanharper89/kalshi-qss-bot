from pathlib import Path
import json
from qseries_v2.oracle_source_network.certification.bounded_dual_runtime_physical_gate import run_gate
r=run_gate(Path.cwd()); print('[DUAL_RUNTIME_GATE]',r)
assert r['base_launcher_boot_alive'] is True
assert r['sports_cycle_completed'] is True
p=Path.cwd()/'qseries_v2/oracle_source_network/state/osn089_bounded_dual_runtime_physical_gate.json'
p.write_text(json.dumps(r,indent=2),encoding='utf-8')
print('[STATE]',p)
print('[PASS] OSN-089 bounded dual-runtime physical gate certified')
