from pathlib import Path
import json,hashlib

root=Path.cwd()
state=json.loads((root/"qseries_v2/oracle_source_network/state/osn091_run_oracle_live_supervision_structure.json").read_text())
p=root/state["launcher_path"]

assert p.exists()
assert hashlib.sha256(p.read_bytes()).hexdigest()==state["launcher_sha256"]
assert state["audit_only"] is True
assert state["launcher_modified"] is False
assert len(state["main_guards"])>=1
assert state["execution_authority"] is False

print("[SHA256]",state["launcher_sha256"])
print("[MAIN_NAMED_FUNCTIONS]",state["main_named_functions"])
print("[MAIN_GUARDS]",state["main_guards"])
print("[SUBPROCESS_CALLS]",state["subprocess_calls"][:20])
print("[THREAD_CALLS]",state["thread_calls"][:20])
print("[PROCESS_CALLS]",state["process_calls"][:20])
print("[RUNTIME_MARKERS]",state["runtime_markers"])
print("[SPORTS_CURRENTLY_INTEGRATED]",state["sports_currently_integrated"])
print("[PASS] run_oracle_LIVE.py structure audited without modification")
print("[PASS] OSN-091 exact supervision structure audit certified")
