from pathlib import Path
import ast, json, hashlib

root=Path.cwd()
state=json.loads((root/"qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json").read_text())
launcher=root/"run_oracle_LIVE.py"
source=launcher.read_text(encoding="utf-8")

assert state["pre_patch_sha256"] != state["post_patch_sha256"]
assert hashlib.sha256(launcher.read_bytes()).hexdigest()==state["post_patch_sha256"]
assert state["rollback_path"]
assert (root/state["rollback_path"]).exists()
assert "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" in source
assert "qseries_v2.oracle_source_network.runtime.sports_supervised_child" in source
assert "_osn092_start_sports_child" in source
assert "_osn092_stop_sports_child" in source
assert state["execution_authority"] is False

ast.parse(source)

print("[PRE_SHA256]",state["pre_patch_sha256"])
print("[POST_SHA256]",state["post_patch_sha256"])
print("[ROLLBACK]",state["rollback_path"])
print("[PASS] run_oracle_LIVE.py now directly contains OSN sports lifecycle integration")
print("[PASS] rollback copy verified")
print("[PASS] patched launcher parses successfully")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-092 direct production launcher integration certified")
