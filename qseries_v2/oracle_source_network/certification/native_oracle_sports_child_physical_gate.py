from pathlib import Path
import subprocess, sys, time, json, hashlib, os, threading, queue

STATE_REL=Path("qseries_v2/oracle_source_network/state/osn095_native_oracle_sports_child_gate.json")
HB_REL=Path("qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json")
S094_REL=Path("qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json")

def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _reader(stream,q):
    try:
        for line in iter(stream.readline,''):
            if not line:
                break
            q.put(line.rstrip("\r\n"))
    finally:
        try:
            stream.close()
        except Exception:
            pass

def run_gate(root=None, startup_timeout=45.0, advance_timeout=55.0):
    base=Path(root or Path.cwd()).resolve()
    launcher=base/"run_oracle_LIVE.py"
    s094=_read_json(base/S094_REL)
    if not s094:
        raise RuntimeError("missing OSN-094 state")

    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()
    expected=s094["post_patch_sha256"]
    if actual!=expected:
        raise RuntimeError(f"run_oracle_LIVE.py hash mismatch expected={expected} actual={actual}")

    hb=base/HB_REL
    before=_read_json(hb) or {}
    pre_cycles=int(before.get("cycles",0) or 0)
    pre_stamp=before.get("last_heartbeat")

    env=os.environ.copy()
    env["PYTHONUNBUFFERED"]="1"

    proc=subprocess.Popen(
        [sys.executable, str(launcher), "--cadence-seconds", "2"],
        cwd=str(base),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    q=queue.Queue()
    t=threading.Thread(target=_reader,args=(proc.stdout,q),daemon=True)
    t.start()

    lines=[]
    first=None
    oracle_reported_sports=False
    start=time.time()

    try:
        while time.time()-start < startup_timeout:
            while True:
                try:
                    line=q.get_nowait()
                except queue.Empty:
                    break
                lines.append(line)
                if "sports=" in line or "sports_restarts=" in line:
                    oracle_reported_sports=True

            if proc.poll() is not None:
                raise RuntimeError(
                    "run_oracle_LIVE.py exited during startup\nOUTPUT:\n"+
                    "\n".join(lines[-200:])
                )

            cur=_read_json(hb)
            if cur:
                c=int(cur.get("cycles",0) or 0)
                stamp=cur.get("last_heartbeat")
                if cur.get("status")=="HEALTHY" and (
                    c > pre_cycles or (stamp and stamp != pre_stamp)
                ):
                    first=cur
                    break
            time.sleep(0.5)

        if not first:
            raise RuntimeError(
                "no new HEALTHY sports heartbeat observed under native Oracle supervision\nOUTPUT:\n"+
                "\n".join(lines[-200:])
            )

        first_cycles=int(first.get("cycles",0) or 0)
        first_stamp=first.get("last_heartbeat")
        end=None
        t2=time.time()

        while time.time()-t2 < advance_timeout:
            while True:
                try:
                    line=q.get_nowait()
                except queue.Empty:
                    break
                lines.append(line)
                if "sports=" in line or "sports_restarts=" in line:
                    oracle_reported_sports=True

            if proc.poll() is not None:
                raise RuntimeError(
                    "run_oracle_LIVE.py exited before second sports cycle\nOUTPUT:\n"+
                    "\n".join(lines[-200:])
                )

            cur=_read_json(hb)
            if cur:
                c=int(cur.get("cycles",0) or 0)
                stamp=cur.get("last_heartbeat")
                if cur.get("status")=="HEALTHY" and c >= first_cycles+1 and stamp != first_stamp:
                    end=cur
                    break
            time.sleep(0.5)

        if not end:
            raise RuntimeError(
                "sports heartbeat did not advance to second cycle under native Oracle supervision\nOUTPUT:\n"+
                "\n".join(lines[-200:])
            )

        while True:
            try:
                line=q.get_nowait()
            except queue.Empty:
                break
            lines.append(line)
            if "sports=" in line or "sports_restarts=" in line:
                oracle_reported_sports=True

        result={
            "launcher":"run_oracle_LIVE.py",
            "launcher_sha256":actual,
            "launcher_process_alive":proc.poll() is None,
            "oracle_reported_sports":oracle_reported_sports,
            "sports_heartbeat_seen":True,
            "sports_status":end.get("status"),
            "sports_cycles_start":first_cycles,
            "sports_cycles_end":int(end.get("cycles",0) or 0),
            "heartbeat_advanced":int(end.get("cycles",0) or 0) >= first_cycles+1,
            "oracle_output_tail":lines[-200:],
            "wrapper_used":False,
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
