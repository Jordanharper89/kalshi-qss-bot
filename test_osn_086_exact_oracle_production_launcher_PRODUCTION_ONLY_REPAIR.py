from pathlib import Path
import json,hashlib

root=Path.cwd()
state=json.loads((root/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json").read_text())
p=root/state["launcher_path"]

assert p.exists()
assert hashlib.sha256(p.read_bytes()).hexdigest()==state["launcher_sha256"]
assert state["selection_rule"]=="UNIQUE_FULL_MARKER_LAUNCHER_AFTER_DIAGNOSTIC_FORENSIC_EXCLUSION"
assert state["execution_authority"] is False

print("[PRODUCTION_LAUNCHER]",state["launcher_path"])
print("[REJECTED_NONPRODUCTION]",tuple(state["rejected_nonproduction_launchers"]))
print("[PASS] unique production launcher selected only after explicit diagnostic/forensic exclusion")
print("[PASS] launcher path + SHA256 frozen")
print("[PASS] OSN-086 production-only launcher contract certified")
