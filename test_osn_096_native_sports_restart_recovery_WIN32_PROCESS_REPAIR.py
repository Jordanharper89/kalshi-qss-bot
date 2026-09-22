
from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_sports_restart_recovery_win32_gate import run_gate

r = run_gate(Path.cwd())
print("[RESULT]", r)

assert r["sports_restarts_after"] >= 1
assert r["sports_healthy_after_restart"] is True
assert r["launcher_alive"] is True
assert r["inspection_method"] == "WIN32_TOOLHELP32"
assert r["wmic_used"] is False
assert r["powershell_used"] is False
assert r["execution_authority"] is False

print("[PASS] Win32 native process inspection used")
print("[PASS] WMIC not used")
print("[PASS] PowerShell not used")
print("[PASS] Oracle native supervisor detected sports child loss")
print("[PASS] sports restart counter advanced")
print("[PASS] replacement sports child returned HEALTHY")
print("[PASS] run_oracle_LIVE.py remained alive")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-096 Win32 process repair certified")
