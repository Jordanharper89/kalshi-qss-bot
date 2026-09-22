from pathlib import Path
from qseries_v2.oracle_source_network.certification.direct_production_launcher_sports_gate import run_gate

result=run_gate(Path.cwd())
print("[DIRECT_PRODUCTION_GATE]",result)

assert result["launcher"]=="run_oracle_LIVE.py"
assert result["launcher_process_alive"] is True
assert result["sports_heartbeat_seen"] is True
assert result["sports_status"]=="HEALTHY"
assert result["sports_cycles_start"] >= 1
assert result["sports_cycles_end"] >= result["sports_cycles_start"] + 1
assert result["heartbeat_advanced"] is True
assert result["wrapper_used"] is False
assert result["execution_authority"] is False

print("[PASS] patched run_oracle_LIVE.py remained alive")
print("[PASS] sports child heartbeat observed under direct production launcher")
print("[PASS] sports heartbeat advanced across repeated durable cycles")
print("[PASS] temporary wrapper was not used")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-093 direct production launcher sports physical recertification certified")
