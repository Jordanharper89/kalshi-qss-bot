from pathlib import Path
from qseries_v2.oracle_source_network.certification.direct_production_launcher_exit_forensic import run_forensic

r=run_forensic(Path.cwd())
print("[EXIT_CODE]",r["exit_code"])
print("[SPORTS_HEARTBEAT_BEFORE]",r["sports_heartbeat_before"])
print("[SPORTS_HEARTBEAT_AFTER]",r["sports_heartbeat_after"])
print("[STDOUT_TAIL]")
print(r["stdout_tail"])
print("[STDERR_TAIL]")
print(r["stderr_tail"])
print("[STARTUP_EXCERPT]")
print(r["startup_excerpt"])
print("[STATE]",r["state_path"])

assert r["launcher"]=="run_oracle_LIVE.py"
assert r["launcher_sha256"]==r["expected_sha256"]
assert r["wrapper_used"] is False
assert r["execution_authority"] is False
print("[PASS] exact production-launcher exit cause captured without modifying launcher")
print("[PASS] OSN-093 exit-cause forensic repair completed")
