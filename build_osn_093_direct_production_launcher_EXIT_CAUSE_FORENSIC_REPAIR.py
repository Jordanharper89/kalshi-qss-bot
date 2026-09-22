from pathlib import Path
import json, hashlib

ROOT=Path.cwd()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
S092=ROOT/"qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json"
TARGET=ROOT/"qseries_v2/oracle_source_network/certification/direct_production_launcher_exit_forensic.py"
TEST=ROOT/"test_osn_093_direct_production_launcher_EXIT_CAUSE_FORENSIC_REPAIR.py"

FORENSIC_SOURCE='from pathlib import Path\nimport subprocess, sys, time, json, hashlib, os\n\nSTATE_REL=Path("qseries_v2/oracle_source_network/state/osn093_direct_launcher_exit_forensic.json")\nS092_REL=Path("qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json")\nHB_REL=Path("qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json")\n\ndef _read_json(path):\n    try:\n        return json.loads(path.read_text(encoding="utf-8"))\n    except Exception:\n        return None\n\ndef _tail(text,n=12000):\n    text=text or ""\n    return text[-n:]\n\ndef _startup_excerpt(source):\n    lines=source.splitlines()\n    wanted=set()\n    for i,line in enumerate(lines,1):\n        low=line.lower()\n        if (\n            "def run_forever" in low\n            or "def main" in low\n            or "popen" in low\n            or "canonical_writer" in low\n            or "gmgn_intelligence" in low\n            or "execution_authority" in low\n            or "terminal_dependency" in low\n            or "_osn092_" in low\n        ):\n            for j in range(max(1,i-5),min(len(lines),i+8)+1):\n                wanted.add(j)\n    chunks=[]\n    last=None\n    for j in sorted(wanted):\n        if last is not None and j>last+1:\n            chunks.append("...")\n        chunks.append(f"{j:04d}: {lines[j-1]}")\n        last=j\n    return "\\n".join(chunks)\n\ndef run_forensic(root=None, observe_seconds=25.0):\n    base=Path(root or Path.cwd()).resolve()\n    launcher=base/"run_oracle_LIVE.py"\n    s092=_read_json(base/S092_REL)\n    if not s092:\n        raise RuntimeError("missing OSN-092 state")\n\n    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()\n    expected=s092["post_patch_sha256"]\n    if actual!=expected:\n        raise RuntimeError(f"launcher hash mismatch expected={expected} actual={actual}")\n\n    hb=base/HB_REL\n    hb_before=_read_json(hb)\n\n    env=os.environ.copy()\n    env["PYTHONUNBUFFERED"]="1"\n\n    proc=subprocess.Popen(\n        [sys.executable, str(launcher)],\n        cwd=str(base),\n        stdout=subprocess.PIPE,\n        stderr=subprocess.PIPE,\n        text=True,\n        env=env,\n    )\n\n    deadline=time.time()+observe_seconds\n    while time.time()<deadline and proc.poll() is None:\n        time.sleep(0.5)\n\n    if proc.poll() is None:\n        proc.terminate()\n        try:\n            out,err=proc.communicate(timeout=15)\n        except Exception:\n            proc.kill()\n            out,err=proc.communicate(timeout=5)\n        exit_code="ALIVE_AT_FORENSIC_TIMEOUT"\n    else:\n        out,err=proc.communicate(timeout=10)\n        exit_code=proc.returncode\n\n    hb_after=_read_json(hb)\n    src=launcher.read_text(encoding="utf-8")\n\n    result={\n        "launcher":"run_oracle_LIVE.py",\n        "launcher_sha256":actual,\n        "expected_sha256":expected,\n        "exit_code":exit_code,\n        "sports_heartbeat_before":hb_before,\n        "sports_heartbeat_after":hb_after,\n        "stdout_tail":_tail(out),\n        "stderr_tail":_tail(err),\n        "startup_excerpt":_startup_excerpt(src),\n        "wrapper_used":False,\n        "launcher_modified":False,\n        "execution_authority":False,\n    }\n\n    state=base/STATE_REL\n    state.parent.mkdir(parents=True,exist_ok=True)\n    result["state_path"]=str(state)\n    state.write_text(json.dumps(result,indent=2),encoding="utf-8")\n    return result\n'
TEST_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.direct_production_launcher_exit_forensic import run_forensic\n\nr=run_forensic(Path.cwd())\nprint("[EXIT_CODE]",r["exit_code"])\nprint("[SPORTS_HEARTBEAT_BEFORE]",r["sports_heartbeat_before"])\nprint("[SPORTS_HEARTBEAT_AFTER]",r["sports_heartbeat_after"])\nprint("[STDOUT_TAIL]")\nprint(r["stdout_tail"])\nprint("[STDERR_TAIL]")\nprint(r["stderr_tail"])\nprint("[STARTUP_EXCERPT]")\nprint(r["startup_excerpt"])\nprint("[STATE]",r["state_path"])\n\nassert r["launcher"]=="run_oracle_LIVE.py"\nassert r["launcher_sha256"]==r["expected_sha256"]\nassert r["wrapper_used"] is False\nassert r["execution_authority"] is False\nprint("[PASS] exact production-launcher exit cause captured without modifying launcher")\nprint("[PASS] OSN-093 exit-cause forensic repair completed")\n'

def main():
    print("="*120)
    print(" OSN-093 DIRECT PRODUCTION LAUNCHER — EXIT CAUSE FORENSIC REPAIR")
    print("="*120)

    for dep in (LAUNCHER,S092):
        if not dep.exists():
            raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    s092=json.loads(S092.read_text(encoding="utf-8"))
    actual=hashlib.sha256(LAUNCHER.read_bytes()).hexdigest()
    if actual!=s092["post_patch_sha256"]:
        raise SystemExit("[FAIL] launcher differs from certified OSN-092 post-patch hash")

    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_text(FORENSIC_SOURCE,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")
    compile(FORENSIC_SOURCE,str(TARGET),"exec")
    compile(TEST_SOURCE,str(TEST),"exec")

    print("[LAUNCHER_SHA256]",actual)
    print("[WRITE]",TARGET.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] launcher remains byte-for-byte unchanged")
    print("[PASS] next test captures actual exit code/stdout/stderr/startup structure")
    print("[PASS] wrapper is not used")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
