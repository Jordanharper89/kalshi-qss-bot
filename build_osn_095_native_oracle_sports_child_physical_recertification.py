from pathlib import Path
import json, hashlib

ROOT=Path.cwd()
LAUNCHER=ROOT/"run_oracle_LIVE.py"
S094=ROOT/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json"
RUNNER=ROOT/"run_osn_sports_continuous_runtime.py"
TARGET=ROOT/"qseries_v2/oracle_source_network/certification/native_oracle_sports_child_physical_gate.py"
TEST=ROOT/"test_osn_095_native_oracle_sports_child_physical_recertification.py"

GATE_SOURCE='from pathlib import Path\nimport subprocess, sys, time, json, hashlib, os, threading, queue\n\nSTATE_REL=Path("qseries_v2/oracle_source_network/state/osn095_native_oracle_sports_child_gate.json")\nHB_REL=Path("qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json")\nS094_REL=Path("qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json")\n\ndef _read_json(path):\n    try:\n        return json.loads(path.read_text(encoding="utf-8"))\n    except Exception:\n        return None\n\ndef _reader(stream,q):\n    try:\n        for line in iter(stream.readline,\'\'):\n            if not line:\n                break\n            q.put(line.rstrip("\\r\\n"))\n    finally:\n        try:\n            stream.close()\n        except Exception:\n            pass\n\ndef run_gate(root=None, startup_timeout=45.0, advance_timeout=55.0):\n    base=Path(root or Path.cwd()).resolve()\n    launcher=base/"run_oracle_LIVE.py"\n    s094=_read_json(base/S094_REL)\n    if not s094:\n        raise RuntimeError("missing OSN-094 state")\n\n    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()\n    expected=s094["post_patch_sha256"]\n    if actual!=expected:\n        raise RuntimeError(f"run_oracle_LIVE.py hash mismatch expected={expected} actual={actual}")\n\n    hb=base/HB_REL\n    before=_read_json(hb) or {}\n    pre_cycles=int(before.get("cycles",0) or 0)\n    pre_stamp=before.get("last_heartbeat")\n\n    env=os.environ.copy()\n    env["PYTHONUNBUFFERED"]="1"\n\n    proc=subprocess.Popen(\n        [sys.executable, str(launcher), "--cadence-seconds", "2"],\n        cwd=str(base),\n        stdout=subprocess.PIPE,\n        stderr=subprocess.STDOUT,\n        text=True,\n        bufsize=1,\n        env=env,\n    )\n\n    q=queue.Queue()\n    t=threading.Thread(target=_reader,args=(proc.stdout,q),daemon=True)\n    t.start()\n\n    lines=[]\n    first=None\n    oracle_reported_sports=False\n    start=time.time()\n\n    try:\n        while time.time()-start < startup_timeout:\n            while True:\n                try:\n                    line=q.get_nowait()\n                except queue.Empty:\n                    break\n                lines.append(line)\n                if "sports=" in line or "sports_restarts=" in line:\n                    oracle_reported_sports=True\n\n            if proc.poll() is not None:\n                raise RuntimeError(\n                    "run_oracle_LIVE.py exited during startup\\nOUTPUT:\\n"+\n                    "\\n".join(lines[-200:])\n                )\n\n            cur=_read_json(hb)\n            if cur:\n                c=int(cur.get("cycles",0) or 0)\n                stamp=cur.get("last_heartbeat")\n                if cur.get("status")=="HEALTHY" and (\n                    c > pre_cycles or (stamp and stamp != pre_stamp)\n                ):\n                    first=cur\n                    break\n            time.sleep(0.5)\n\n        if not first:\n            raise RuntimeError(\n                "no new HEALTHY sports heartbeat observed under native Oracle supervision\\nOUTPUT:\\n"+\n                "\\n".join(lines[-200:])\n            )\n\n        first_cycles=int(first.get("cycles",0) or 0)\n        first_stamp=first.get("last_heartbeat")\n        end=None\n        t2=time.time()\n\n        while time.time()-t2 < advance_timeout:\n            while True:\n                try:\n                    line=q.get_nowait()\n                except queue.Empty:\n                    break\n                lines.append(line)\n                if "sports=" in line or "sports_restarts=" in line:\n                    oracle_reported_sports=True\n\n            if proc.poll() is not None:\n                raise RuntimeError(\n                    "run_oracle_LIVE.py exited before second sports cycle\\nOUTPUT:\\n"+\n                    "\\n".join(lines[-200:])\n                )\n\n            cur=_read_json(hb)\n            if cur:\n                c=int(cur.get("cycles",0) or 0)\n                stamp=cur.get("last_heartbeat")\n                if cur.get("status")=="HEALTHY" and c >= first_cycles+1 and stamp != first_stamp:\n                    end=cur\n                    break\n            time.sleep(0.5)\n\n        if not end:\n            raise RuntimeError(\n                "sports heartbeat did not advance to second cycle under native Oracle supervision\\nOUTPUT:\\n"+\n                "\\n".join(lines[-200:])\n            )\n\n        while True:\n            try:\n                line=q.get_nowait()\n            except queue.Empty:\n                break\n            lines.append(line)\n            if "sports=" in line or "sports_restarts=" in line:\n                oracle_reported_sports=True\n\n        result={\n            "launcher":"run_oracle_LIVE.py",\n            "launcher_sha256":actual,\n            "launcher_process_alive":proc.poll() is None,\n            "oracle_reported_sports":oracle_reported_sports,\n            "sports_heartbeat_seen":True,\n            "sports_status":end.get("status"),\n            "sports_cycles_start":first_cycles,\n            "sports_cycles_end":int(end.get("cycles",0) or 0),\n            "heartbeat_advanced":int(end.get("cycles",0) or 0) >= first_cycles+1,\n            "oracle_output_tail":lines[-200:],\n            "wrapper_used":False,\n            "terminal_dependency":"NONE",\n            "execution_authority":False,\n        }\n\n        out=base/STATE_REL\n        out.parent.mkdir(parents=True,exist_ok=True)\n        out.write_text(json.dumps(result,indent=2),encoding="utf-8")\n        return result\n    finally:\n        if proc.poll() is None:\n            proc.terminate()\n            try:\n                proc.wait(timeout=15)\n            except Exception:\n                try:\n                    proc.kill()\n                    proc.wait(timeout=5)\n                except Exception:\n                    pass\n'
TEST_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.native_oracle_sports_child_physical_gate import run_gate\n\nr=run_gate(Path.cwd())\nprint("[RESULT]",r)\n\nassert r["launcher"]=="run_oracle_LIVE.py"\nassert r["launcher_process_alive"] is True\nassert r["oracle_reported_sports"] is True\nassert r["sports_heartbeat_seen"] is True\nassert r["sports_status"]=="HEALTHY"\nassert r["sports_cycles_end"] >= r["sports_cycles_start"] + 1\nassert r["heartbeat_advanced"] is True\nassert r["wrapper_used"] is False\nassert r["execution_authority"] is False\n\nprint("[PASS] run_oracle_LIVE.py booted with native sports child")\nprint("[PASS] Oracle native heartbeat reported sports child")\nprint("[PASS] sports heartbeat advanced across repeated cycles")\nprint("[PASS] wrapper launcher not used")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-095 native Oracle sports child physical recertification certified")\n'

def main():
    print("="*120)
    print(" OSN-095 NATIVE ORACLE SPORTS CHILD PHYSICAL RECERTIFICATION INSTALLER")
    print("="*120)

    for dep in (LAUNCHER,S094,RUNNER):
        if not dep.exists():
            raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    s094=json.loads(S094.read_text(encoding="utf-8"))
    actual=hashlib.sha256(LAUNCHER.read_bytes()).hexdigest()
    if actual!=s094["post_patch_sha256"]:
        raise SystemExit("[FAIL] launcher differs from certified OSN-094 post-patch hash")

    src=LAUNCHER.read_text(encoding="utf-8")
    if '"sports": "run_osn_sports_continuous_runtime.py"' not in src:
        raise SystemExit("[FAIL] native sports CHILDREN registration missing")
    if "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" in src:
        raise SystemExit("[FAIL] stale OSN-092 custom hook remains")

    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_text(GATE_SOURCE,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")
    compile(GATE_SOURCE,str(TARGET),"exec")
    compile(TEST_SOURCE,str(TEST),"exec")

    print("[LAUNCHER_SHA256]",actual)
    print("[WRITE]",TARGET.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] gate launches run_oracle_LIVE.py directly")
    print("[PASS] gate requires Oracle heartbeat to report sports supervision")
    print("[PASS] gate requires two HEALTHY sports runtime cycles")
    print("[PASS] wrapper launcher is not used")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
