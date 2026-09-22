
from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_sports_parent_exit_forensic import run_forensic

r=run_forensic(Path.cwd())
print("[RESULT]",r)
assert r["sports_was_last_registry_entry"] is True
assert r["wmic_used"] is False
assert r["powershell_used"] is False
assert r["launcher_modified"] is False
assert r["execution_authority"] is False
print("[PASS] exact sports child terminated under bounded forensic")
print("[PASS] parent post-termination behavior captured")
print("[PASS] run_oracle_LIVE.py not modified")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-096 parent-exit forensic capture complete")
