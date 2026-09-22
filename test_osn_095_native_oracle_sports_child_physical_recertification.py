from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_oracle_sports_child_physical_gate import run_gate

r=run_gate(Path.cwd())
print("[RESULT]",r)

assert r["launcher"]=="run_oracle_LIVE.py"
assert r["launcher_process_alive"] is True
assert r["oracle_reported_sports"] is True
assert r["sports_heartbeat_seen"] is True
assert r["sports_status"]=="HEALTHY"
assert r["sports_cycles_end"] >= r["sports_cycles_start"] + 1
assert r["heartbeat_advanced"] is True
assert r["wrapper_used"] is False
assert r["execution_authority"] is False

print("[PASS] run_oracle_LIVE.py booted with native sports child")
print("[PASS] Oracle native heartbeat reported sports child")
print("[PASS] sports heartbeat advanced across repeated cycles")
print("[PASS] wrapper launcher not used")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-095 native Oracle sports child physical recertification certified")
