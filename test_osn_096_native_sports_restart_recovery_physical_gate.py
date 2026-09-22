
from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_sports_restart_recovery_gate import run_gate
r=run_gate(Path.cwd());print("[RESULT]",r)
assert r["sports_pid_before"]!=r["sports_pid_after"]
assert r["sports_restarts_after"]>=1
assert r["sports_healthy_after_restart"] is True
assert r["launcher_alive"] is True
assert r["execution_authority"] is False
print("[PASS] native supervisor restarted terminated sports child")
print("[PASS] replacement sports child returned HEALTHY")
print("[PASS] production launcher remained alive")
print("[PASS] OSN-096 restart/recovery physical gate certified")
