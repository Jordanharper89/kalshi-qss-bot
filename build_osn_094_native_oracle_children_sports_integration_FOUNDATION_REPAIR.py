from pathlib import Path
import json, hashlib, shutil, re, ast

ROOT=Path.cwd()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
S092=ROOT/"qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json"
FORENSIC=ROOT/"qseries_v2/oracle_source_network/state/osn093_direct_launcher_exit_forensic.json"
RUNNER=ROOT/"run_osn_sports_continuous_runtime.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json"
ROLLBACK_DIR=ROOT/"qseries_v2/oracle_source_network/rollback"
TEST=ROOT/"test_osn_094_native_oracle_children_sports_integration_FOUNDATION_REPAIR.py"

RUNNER_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_forever\n\nif __name__=="__main__":\n    run_forever(\n        root=Path.cwd(),\n        cadence_seconds=30.0,\n        timeout=15,\n    )\n'
TEST_SOURCE='from pathlib import Path\nimport ast, json, hashlib\n\nroot=Path.cwd()\nstate=json.loads((root/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json").read_text())\nlauncher=root/"run_oracle_LIVE.py"\nrunner=root/"run_osn_sports_continuous_runtime.py"\nsrc=launcher.read_text(encoding="utf-8")\n\nassert hashlib.sha256(launcher.read_bytes()).hexdigest()==state["post_patch_sha256"]\nassert runner.exists()\nassert \'"sports":"run_osn_sports_continuous_runtime.py"\' in src.replace(" ","")\nassert "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" not in src\nassert "_osn092_run_main_with_sports" not in src\nassert "raise SystemExit(main())" in src\nassert state["integration_mode"]=="NATIVE_CHILDREN_REGISTRY"\nassert state["execution_authority"] is False\n\nast.parse(src)\nast.parse(runner.read_text(encoding="utf-8"))\n\nprint("[PRE_SHA256]",state["pre_patch_sha256"])\nprint("[POST_SHA256]",state["post_patch_sha256"])\nprint("[ROLLBACK]",state["rollback_path"])\nprint("[RUNNER]",state["sports_runner"])\nprint("[PASS] OSN-092 custom lifecycle hook retired")\nprint("[PASS] sports registered in native Oracle CHILDREN supervision")\nprint("[PASS] production main guard restored to main()")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-094 native Oracle child integration certified")\n'

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    print("="*120)
    print(" OSN-094 NATIVE ORACLE CHILDREN SPORTS INTEGRATION — FOUNDATION REPAIR")
    print("="*120)

    for dep in (LAUNCHER,S092,FORENSIC):
        if not dep.exists():
            raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    s092=json.loads(S092.read_text(encoding="utf-8"))
    forensic=json.loads(FORENSIC.read_text(encoding="utf-8"))

    pre_sha=sha256(LAUNCHER)
    if pre_sha!=s092["post_patch_sha256"]:
        raise SystemExit("[FAIL] launcher hash is not exact OSN-092 post-patch image")

    stderr=forensic.get("stderr_tail","")
    if "NameError: name 'ROOT' is not defined" not in stderr:
        raise SystemExit("[FAIL] OSN-093 forensic does not prove expected ROOT NameError")

    source=LAUNCHER.read_text(encoding="utf-8")
    if "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" not in source:
        raise SystemExit("[FAIL] expected OSN-092 custom block not present")

    # Preserve exact failed integrated image before foundational repair.
    ROLLBACK_DIR.mkdir(parents=True,exist_ok=True)
    rollback_rel=Path("qseries_v2/oracle_source_network/rollback")/("run_oracle_LIVE_pre_osn094_"+pre_sha[:16]+".py")
    rollback=ROOT/rollback_rel
    shutil.copy2(LAUNCHER,rollback)
    if sha256(rollback)!=pre_sha:
        raise SystemExit("[FAIL] rollback hash mismatch")

    # Write the dedicated child runner used by the existing Oracle supervisor.
    RUNNER.write_text(RUNNER_SOURCE,encoding="utf-8")
    compile(RUNNER_SOURCE,str(RUNNER),"exec")

    # Remove the entire OSN-092 custom lifecycle block.
    begin="# ============================== OSN-092 DIRECT SPORTS INTEGRATION BEGIN =============================="
    end="# =============================== OSN-092 DIRECT SPORTS INTEGRATION END ==============================="
    a=source.find(begin)
    b=source.find(end)
    if a<0 or b<0 or b<a:
        raise SystemExit("[FAIL] unable to locate exact OSN-092 block")
    b=b+len(end)
    source=(source[:a].rstrip()+"\n\n"+source[b:].lstrip())

    # Restore original production main guard.
    source=source.replace(
        "raise SystemExit(_osn092_run_main_with_sports())",
        "raise SystemExit(main())",
        1
    )

    # Register sports in the existing native CHILDREN dictionary.
    if '"sports"' in source or "'sports'" in source:
        raise SystemExit("[FAIL] sports key already present in launcher CHILDREN registry")

    anchor='    "gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py",'
    if anchor not in source:
        raise SystemExit("[FAIL] exact CHILDREN registry anchor not found")

    source=source.replace(
        anchor,
        anchor+'\n    "sports": "run_osn_sports_continuous_runtime.py",',
        1
    )

    # Structural verification before write.
    ast.parse(source)
    if source.count('"sports": "run_osn_sports_continuous_runtime.py"')!=1:
        raise SystemExit("[FAIL] sports CHILDREN registration count is not exactly one")
    if "_osn092_" in source:
        raise SystemExit("[FAIL] stale OSN-092 lifecycle symbols remain")

    LAUNCHER.write_text(source,encoding="utf-8")
    post_sha=sha256(LAUNCHER)

    state={
        "launcher_path":"run_oracle_LIVE.py",
        "pre_patch_sha256":pre_sha,
        "post_patch_sha256":post_sha,
        "rollback_path":rollback_rel.as_posix(),
        "sports_runner":"run_osn_sports_continuous_runtime.py",
        "integration_mode":"NATIVE_CHILDREN_REGISTRY",
        "native_supervision_inherited":[
            "_start",
            "_spawn",
            "restart_counts",
            "runtime health state",
            "operator shutdown"
        ],
        "osn092_custom_lifecycle_retired":True,
        "main_guard_restored":True,
        "terminal_dependency":"NONE",
        "execution_authority":False
    }

    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,indent=2),encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")
    compile(TEST_SOURCE,str(TEST),"exec")

    print("[ROOT_CAUSE] OSN-092 custom child hook referenced undefined ROOT")
    print("[REPAIR] retired custom lifecycle hook")
    print("[REPAIR] added sports to existing Oracle CHILDREN registry")
    print("[RUNNER]",RUNNER.name)
    print("[ROLLBACK]",rollback_rel)
    print("[PRE_SHA256]",pre_sha)
    print("[POST_SHA256]",post_sha)
    print("[STATE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] native Oracle supervision reused")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
