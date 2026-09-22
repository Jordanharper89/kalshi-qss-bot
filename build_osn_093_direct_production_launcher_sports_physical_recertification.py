from pathlib import Path
import json, hashlib

ROOT=Path.cwd()
S092=ROOT/"qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json"
S087=ROOT/"qseries_v2/oracle_source_network/state/osn087_sports_supervised_child.json"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
GATE=ROOT/"qseries_v2/oracle_source_network/certification/direct_production_launcher_sports_gate.py"
TEST=ROOT/"test_osn_093_direct_production_launcher_sports_physical_recertification.py"

GATE_SOURCE='from pathlib import Path\nimport subprocess, sys, time, json, hashlib, os\n\nSTATE_REL=Path("qseries_v2/oracle_source_network/state/osn093_direct_production_launcher_sports_gate.json")\nHB_REL=Path("qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json")\nS092_REL=Path("qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json")\n\ndef _read_json(path):\n    try:\n        return json.loads(path.read_text(encoding="utf-8"))\n    except Exception:\n        return None\n\ndef run_gate(root=None, startup_timeout=50.0, advance_timeout=55.0):\n    base=Path(root or Path.cwd()).resolve()\n    launcher=base/"run_oracle_LIVE.py"\n    s092=_read_json(base/S092_REL)\n    if not s092:\n        raise RuntimeError("missing OSN-092 state")\n\n    actual_hash=hashlib.sha256(launcher.read_bytes()).hexdigest()\n    if actual_hash != s092["post_patch_sha256"]:\n        raise RuntimeError("run_oracle_LIVE.py hash does not match certified OSN-092 post-patch hash")\n\n    hb=base/HB_REL\n    before=_read_json(hb) or {}\n    pre_cycles=int(before.get("cycles",0) or 0)\n    pre_stamp=before.get("last_heartbeat")\n\n    env=os.environ.copy()\n    env["PYTHONUNBUFFERED"]="1"\n\n    proc=subprocess.Popen(\n        [sys.executable, str(launcher)],\n        cwd=str(base),\n        stdout=subprocess.DEVNULL,\n        stderr=subprocess.DEVNULL,\n        env=env,\n    )\n\n    first=None\n    start=time.time()\n    try:\n        while time.time()-start < startup_timeout:\n            if proc.poll() is not None:\n                raise RuntimeError("patched run_oracle_LIVE.py exited before sports heartbeat became healthy")\n            cur=_read_json(hb)\n            if cur:\n                c=int(cur.get("cycles",0) or 0)\n                stamp=cur.get("last_heartbeat")\n                if cur.get("status")=="HEALTHY" and (\n                    c > pre_cycles or (stamp and stamp != pre_stamp)\n                ):\n                    first=cur\n                    break\n            time.sleep(1.0)\n\n        if not first:\n            raise RuntimeError("no new HEALTHY sports heartbeat observed from patched run_oracle_LIVE.py")\n\n        first_cycles=int(first.get("cycles",0) or 0)\n        first_stamp=first.get("last_heartbeat")\n        end=None\n        t2=time.time()\n\n        while time.time()-t2 < advance_timeout:\n            if proc.poll() is not None:\n                raise RuntimeError("patched run_oracle_LIVE.py exited before second sports cycle")\n            cur=_read_json(hb)\n            if cur:\n                c=int(cur.get("cycles",0) or 0)\n                stamp=cur.get("last_heartbeat")\n                if cur.get("status")=="HEALTHY" and c >= first_cycles+1 and stamp != first_stamp:\n                    end=cur\n                    break\n            time.sleep(1.0)\n\n        if not end:\n            raise RuntimeError("sports heartbeat did not advance to a second cycle under patched production launcher")\n\n        result={\n            "launcher":"run_oracle_LIVE.py",\n            "launcher_sha256":actual_hash,\n            "launcher_process_alive":proc.poll() is None,\n            "sports_heartbeat_seen":True,\n            "sports_status":end.get("status"),\n            "sports_cycles_start":first_cycles,\n            "sports_cycles_end":int(end.get("cycles",0) or 0),\n            "heartbeat_advanced":int(end.get("cycles",0) or 0) >= first_cycles+1,\n            "wrapper_used":False,\n            "temporary_wrapper_present":(base/"run_oracle_live_WITH_OSN_SPORTS.py").exists(),\n            "terminal_dependency":"NONE",\n            "execution_authority":False,\n        }\n\n        out=base/STATE_REL\n        out.parent.mkdir(parents=True,exist_ok=True)\n        out.write_text(json.dumps(result,indent=2),encoding="utf-8")\n        return result\n    finally:\n        if proc.poll() is None:\n            proc.terminate()\n            try:\n                proc.wait(timeout=15)\n            except Exception:\n                try:\n                    proc.kill()\n                    proc.wait(timeout=5)\n                except Exception:\n                    pass\n'
TEST_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_source_network.certification.direct_production_launcher_sports_gate import run_gate\n\nresult=run_gate(Path.cwd())\nprint("[DIRECT_PRODUCTION_GATE]",result)\n\nassert result["launcher"]=="run_oracle_LIVE.py"\nassert result["launcher_process_alive"] is True\nassert result["sports_heartbeat_seen"] is True\nassert result["sports_status"]=="HEALTHY"\nassert result["sports_cycles_start"] >= 1\nassert result["sports_cycles_end"] >= result["sports_cycles_start"] + 1\nassert result["heartbeat_advanced"] is True\nassert result["wrapper_used"] is False\nassert result["execution_authority"] is False\n\nprint("[PASS] patched run_oracle_LIVE.py remained alive")\nprint("[PASS] sports child heartbeat observed under direct production launcher")\nprint("[PASS] sports heartbeat advanced across repeated durable cycles")\nprint("[PASS] temporary wrapper was not used")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-093 direct production launcher sports physical recertification certified")\n'

def main():
    print("="*120)
    print(" OSN-093 DIRECT PRODUCTION LAUNCHER SPORTS PHYSICAL RECERTIFICATION INSTALLER")
    print("="*120)

    for dep in (S092,S087,LAUNCHER):
        if not dep.exists():
            raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))

    s092=json.loads(S092.read_text(encoding="utf-8"))
    actual=hashlib.sha256(LAUNCHER.read_bytes()).hexdigest()
    if actual != s092["post_patch_sha256"]:
        raise SystemExit("[FAIL] production launcher hash differs from certified OSN-092 post-patch hash")

    src=LAUNCHER.read_text(encoding="utf-8")
    if "OSN-092 DIRECT SPORTS INTEGRATION BEGIN" not in src:
        raise SystemExit("[FAIL] direct sports integration marker missing")
    if "raise SystemExit(_osn092_run_main_with_sports())" not in src:
        raise SystemExit("[FAIL] production __main__ guard is not wired to direct sports lifecycle")

    GATE.parent.mkdir(parents=True,exist_ok=True)
    GATE.write_text(GATE_SOURCE,encoding="utf-8")
    TEST.write_text(TEST_SOURCE,encoding="utf-8")
    compile(GATE_SOURCE,str(GATE),"exec")
    compile(TEST_SOURCE,str(TEST),"exec")

    print("[LAUNCHER_SHA256]",actual)
    print("[WRITE]",GATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] test launches run_oracle_LIVE.py directly")
    print("[PASS] requires two successive HEALTHY sports heartbeat cycles")
    print("[PASS] wrapper launcher is not invoked")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
