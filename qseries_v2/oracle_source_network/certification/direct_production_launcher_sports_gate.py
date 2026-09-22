from pathlib import Path
import subprocess, sys, time, json, hashlib, os

STATE_REL=Path("qseries_v2/oracle_source_network/state/osn093_direct_production_launcher_sports_gate.json")
HB_REL=Path("qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json")
S092_REL=Path("qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json")

def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def run_gate(root=None, startup_timeout=50.0, advance_timeout=55.0):
    base=Path(root or Path.cwd()).resolve()
    launcher=base/"run_oracle_LIVE.py"
    s092=_read_json(base/S092_REL)
    if not s092:
        raise RuntimeError("missing OSN-092 state")

    actual_hash=hashlib.sha256(launcher.read_bytes()).hexdigest()
    if actual_hash != s092["post_patch_sha256"]:
        raise RuntimeError("run_oracle_LIVE.py hash does not match certified OSN-092 post-patch hash")

    hb=base/HB_REL
    before=_read_json(hb) or {}
    pre_cycles=int(before.get("cycles",0) or 0)
    pre_stamp=before.get("last_heartbeat")

    env=os.environ.copy()
    env["PYTHONUNBUFFERED"]="1"

    proc=subprocess.Popen(
        [sys.executable, str(launcher)],
        cwd=str(base),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    first=None
    start=time.time()
    try:
        while time.time()-start < startup_timeout:
            if proc.poll() is not None:
                raise RuntimeError("patched run_oracle_LIVE.py exited before sports heartbeat became healthy")
            cur=_read_json(hb)
            if cur:
                c=int(cur.get("cycles",0) or 0)
                stamp=cur.get("last_heartbeat")
                if cur.get("status")=="HEALTHY" and (
                    c > pre_cycles or (stamp and stamp != pre_stamp)
                ):
                    first=cur
                    break
            time.sleep(1.0)

        if not first:
            raise RuntimeError("no new HEALTHY sports heartbeat observed from patched run_oracle_LIVE.py")

        first_cycles=int(first.get("cycles",0) or 0)
        first_stamp=first.get("last_heartbeat")
        end=None
        t2=time.time()

        while time.time()-t2 < advance_timeout:
            if proc.poll() is not None:
                raise RuntimeError("patched run_oracle_LIVE.py exited before second sports cycle")
            cur=_read_json(hb)
            if cur:
                c=int(cur.get("cycles",0) or 0)
                stamp=cur.get("last_heartbeat")
                if cur.get("status")=="HEALTHY" and c >= first_cycles+1 and stamp != first_stamp:
                    end=cur
                    break
            time.sleep(1.0)

        if not end:
            raise RuntimeError("sports heartbeat did not advance to a second cycle under patched production launcher")

        result={
            "launcher":"run_oracle_LIVE.py",
            "launcher_sha256":actual_hash,
            "launcher_process_alive":proc.poll() is None,
            "sports_heartbeat_seen":True,
            "sports_status":end.get("status"),
            "sports_cycles_start":first_cycles,
            "sports_cycles_end":int(end.get("cycles",0) or 0),
            "heartbeat_advanced":int(end.get("cycles",0) or 0) >= first_cycles+1,
            "wrapper_used":False,
            "temporary_wrapper_present":(base/"run_oracle_live_WITH_OSN_SPORTS.py").exists(),
            "terminal_dependency":"NONE",
            "execution_authority":False,
        }

        out=base/STATE_REL
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,indent=2),encoding="utf-8")
        return result
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except Exception:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass
