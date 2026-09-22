
from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_sports_restart_recovery_exact_last_child_gate import run_gate

r=run_gate(Path.cwd())
print("[RESULT]",r)
assert r["sports_was_last_registry_entry"] is True
assert r["children_registry_order"][-1]=="sports"
assert r["sports_pid_before"] != r["sports_pid_after"]
assert r["sports_restarts_after"] >= 1
assert r["sports_healthy_after_restart"] is True
assert r["launcher_alive"] is True
assert r["wmic_used"] is False
assert r["powershell_used"] is False
assert r["execution_authority"] is False
print("[PASS] sports proven final native CHILDREN entry")
print("[PASS] exact final-spawned sports child terminated")
print("[PASS] sports_restarts advanced")
print("[PASS] replacement sports child returned HEALTHY")
print("[PASS] production launcher remained alive")
print("[PASS] WMIC/PowerShell not used")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-096 exact-last-child restart/recovery repair certified")
