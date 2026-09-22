from pathlib import Path
import ast, json, hashlib

root=Path.cwd()
state=json.loads((root/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json").read_text())
launcher=root/"run_oracle_LIVE.py"
runner=root/"run_osn_sports_continuous_runtime.py"
src=launcher.read_text(encoding="utf-8")

assert hashlib.sha256(launcher.read_bytes()).hexdigest()==state["post_patch_sha256"]
assert runner.exists()
assert '"sports":"run_osn_sports_continuous_runtime.py"' in src.replace(" ","")
assert "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" not in src
assert "_osn092_run_main_with_sports" not in src
assert "raise SystemExit(main())" in src
assert state["integration_mode"]=="NATIVE_CHILDREN_REGISTRY"
assert state["execution_authority"] is False

ast.parse(src)
ast.parse(runner.read_text(encoding="utf-8"))

print("[PRE_SHA256]",state["pre_patch_sha256"])
print("[POST_SHA256]",state["post_patch_sha256"])
print("[ROLLBACK]",state["rollback_path"])
print("[RUNNER]",state["sports_runner"])
print("[PASS] OSN-092 custom lifecycle hook retired")
print("[PASS] sports registered in native Oracle CHILDREN supervision")
print("[PASS] production main guard restored to main()")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-094 native Oracle child integration certified")
