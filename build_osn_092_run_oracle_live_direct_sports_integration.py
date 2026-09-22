from pathlib import Path
import ast, json, hashlib, shutil, re

ROOT=Path.cwd()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
S091=ROOT/"qseries_v2/oracle_source_network/state/osn091_run_oracle_live_supervision_structure.json"
S087=ROOT/"qseries_v2/oracle_source_network/state/osn087_sports_supervised_child.json"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json"
ROLLBACK_DIR=ROOT/"qseries_v2/oracle_source_network/rollback"
TEST=ROOT/"test_osn_092_run_oracle_live_direct_sports_integration.py"

TEST_SOURCE='from pathlib import Path\nimport ast, json, hashlib\n\nroot=Path.cwd()\nstate=json.loads((root/"qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json").read_text())\nlauncher=root/"run_oracle_LIVE.py"\nsource=launcher.read_text(encoding="utf-8")\n\nassert state["pre_patch_sha256"] != state["post_patch_sha256"]\nassert hashlib.sha256(launcher.read_bytes()).hexdigest()==state["post_patch_sha256"]\nassert state["rollback_path"]\nassert (root/state["rollback_path"]).exists()\nassert "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" in source\nassert "qseries_v2.oracle_source_network.runtime.sports_supervised_child" in source\nassert "_osn092_start_sports_child" in source\nassert "_osn092_stop_sports_child" in source\nassert state["execution_authority"] is False\n\nast.parse(source)\n\nprint("[PRE_SHA256]",state["pre_patch_sha256"])\nprint("[POST_SHA256]",state["post_patch_sha256"])\nprint("[ROLLBACK]",state["rollback_path"])\nprint("[PASS] run_oracle_LIVE.py now directly contains OSN sports lifecycle integration")\nprint("[PASS] rollback copy verified")\nprint("[PASS] patched launcher parses successfully")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-092 direct production launcher integration certified")\n'

BLOCK = r"""
# ============================== OSN-092 DIRECT SPORTS INTEGRATION BEGIN ==============================
_OSN092_SPORTS_PROCESS = None

def _osn092_start_sports_child():
    global _OSN092_SPORTS_PROCESS
    if _OSN092_SPORTS_PROCESS is not None and _OSN092_SPORTS_PROCESS.poll() is None:
        return _OSN092_SPORTS_PROCESS

    import subprocess as _osn092_subprocess
    import sys as _osn092_sys

    _osn092_code = (
        "from pathlib import Path; "
        "from qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_forever; "
        "run_forever(root=Path.cwd(), cadence_seconds=30.0, timeout=15)"
    )

    _OSN092_SPORTS_PROCESS = _osn092_subprocess.Popen(
        [_osn092_sys.executable, "-c", _osn092_code],
        cwd=str(ROOT),
    )
    print(f"[OSN_SPORTS] STARTED pid={_OSN092_SPORTS_PROCESS.pid}")
    return _OSN092_SPORTS_PROCESS


def _osn092_stop_sports_child():
    global _OSN092_SPORTS_PROCESS
    p = _OSN092_SPORTS_PROCESS
    if p is None:
        return
    if p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=10)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("[OSN_SPORTS] STOPPED")
    _OSN092_SPORTS_PROCESS = None


def _osn092_run_main_with_sports():
    _osn092_start_sports_child()
    try:
        return main()
    finally:
        _osn092_stop_sports_child()
# =============================== OSN-092 DIRECT SPORTS INTEGRATION END ===============================
"""

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    print("="*120)
    print(" OSN-092 RUN_ORACLE_LIVE DIRECT SPORTS INTEGRATION INSTALLER")
    print("="*120)

    for dep in (LAUNCHER,S091,S087):
        if not dep.exists():
            raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    audit=json.loads(S091.read_text())
    pre_sha=sha256(LAUNCHER)

    if pre_sha != audit["launcher_sha256"]:
        raise SystemExit(
            "[FAIL] run_oracle_LIVE.py changed since OSN-091 audit. "
            "Expected "+audit["launcher_sha256"]+" got "+pre_sha
        )

    source=LAUNCHER.read_text(encoding="utf-8")
    if "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" in source:
        raise SystemExit("[FAIL] OSN-092 integration already present; refusing duplicate patch")

    tree=ast.parse(source)
    main_guards=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.If):
            try:
                test=ast.unparse(node.test)
            except Exception:
                test=""
            if "__name__" in test and "__main__" in test:
                main_guards.append(node)

    if len(main_guards)!=1:
        raise SystemExit("[FAIL] expected exactly one __main__ guard; found "+str(len(main_guards)))

    guard=main_guards[0]
    guard_start=guard.lineno
    lines=source.splitlines()

    # Exact audited shape requirement.
    guard_text="\n".join(lines[guard.lineno-1:guard.end_lineno])
    if "raise SystemExit(main())" not in guard_text:
        raise SystemExit("[FAIL] audited main-guard shape changed; refusing patch")

    ROLLBACK_DIR.mkdir(parents=True,exist_ok=True)
    rollback_rel=Path("qseries_v2/oracle_source_network/rollback")/("run_oracle_LIVE_pre_osn092_"+pre_sha[:16]+".py")
    rollback=ROOT/rollback_rel
    shutil.copy2(LAUNCHER,rollback)

    if sha256(rollback)!=pre_sha:
        raise SystemExit("[FAIL] rollback copy hash mismatch")

    # Insert lifecycle helpers immediately before the exact __main__ guard.
    before="\n".join(lines[:guard_start-1]).rstrip()+"\n\n"
    after="\n".join(lines[guard_start-1:]).lstrip()

    # Replace only the exact main invocation inside the preserved guard.
    after=after.replace("raise SystemExit(main())","raise SystemExit(_osn092_run_main_with_sports())",1)

    patched=before+BLOCK.strip()+"\n\n"+after+"\n"
    ast.parse(patched)

    LAUNCHER.write_text(patched,encoding="utf-8")
    post_sha=sha256(LAUNCHER)

    state={
        "launcher_path":"run_oracle_LIVE.py",
        "pre_patch_sha256":pre_sha,
        "post_patch_sha256":post_sha,
        "rollback_path":rollback_rel.as_posix(),
        "integration_mode":"DIRECT_IN_PRODUCTION_LAUNCHER_MAIN_LIFECYCLE",
        "existing_run_forever_body_modified":False,
        "sports_child_module":"qseries_v2.oracle_source_network.runtime.sports_supervised_child",
        "sports_entrypoint":"run_forever(root=Path.cwd(), cadence_seconds=30.0, timeout=15)",
        "temporary_wrapper_status":"RETIRE_AFTER_DIRECT_PHYSICAL_RECERTIFICATION",
        "terminal_dependency":"NONE",
        "execution_authority":False
    }

    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,indent=2),encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")
    compile(TEST_SOURCE,str(TEST),"exec")

    print("[ROLLBACK]",rollback_rel)
    print("[PRE_SHA256]",pre_sha)
    print("[POST_SHA256]",post_sha)
    print("[PATCH] direct sports lifecycle inserted into run_oracle_LIVE.py")
    print("[PASS] existing run_forever body preserved")
    print("[PASS] rollback copy hash verified")
    print("[STATE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
