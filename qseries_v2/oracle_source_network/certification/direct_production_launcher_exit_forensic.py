from pathlib import Path
import subprocess, sys, time, json, hashlib, os

STATE_REL=Path("qseries_v2/oracle_source_network/state/osn093_direct_launcher_exit_forensic.json")
S092_REL=Path("qseries_v2/oracle_source_network/state/osn092_run_oracle_live_direct_sports_integration.json")
HB_REL=Path("qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json")

def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _tail(text,n=12000):
    text=text or ""
    return text[-n:]

def _startup_excerpt(source):
    lines=source.splitlines()
    wanted=set()
    for i,line in enumerate(lines,1):
        low=line.lower()
        if (
            "def run_forever" in low
            or "def main" in low
            or "popen" in low
            or "canonical_writer" in low
            or "gmgn_intelligence" in low
            or "execution_authority" in low
            or "terminal_dependency" in low
            or "_osn092_" in low
        ):
            for j in range(max(1,i-5),min(len(lines),i+8)+1):
                wanted.add(j)
    chunks=[]
    last=None
    for j in sorted(wanted):
        if last is not None and j>last+1:
            chunks.append("...")
        chunks.append(f"{j:04d}: {lines[j-1]}")
        last=j
    return "\n".join(chunks)

def run_forensic(root=None, observe_seconds=25.0):
    base=Path(root or Path.cwd()).resolve()
    launcher=base/"run_oracle_LIVE.py"
    s092=_read_json(base/S092_REL)
    if not s092:
        raise RuntimeError("missing OSN-092 state")

    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()
    expected=s092["post_patch_sha256"]
    if actual!=expected:
        raise RuntimeError(f"launcher hash mismatch expected={expected} actual={actual}")

    hb=base/HB_REL
    hb_before=_read_json(hb)

    env=os.environ.copy()
    env["PYTHONUNBUFFERED"]="1"

    proc=subprocess.Popen(
        [sys.executable, str(launcher)],
        cwd=str(base),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    deadline=time.time()+observe_seconds
    while time.time()<deadline and proc.poll() is None:
        time.sleep(0.5)

    if proc.poll() is None:
        proc.terminate()
        try:
            out,err=proc.communicate(timeout=15)
        except Exception:
            proc.kill()
            out,err=proc.communicate(timeout=5)
        exit_code="ALIVE_AT_FORENSIC_TIMEOUT"
    else:
        out,err=proc.communicate(timeout=10)
        exit_code=proc.returncode

    hb_after=_read_json(hb)
    src=launcher.read_text(encoding="utf-8")

    result={
        "launcher":"run_oracle_LIVE.py",
        "launcher_sha256":actual,
        "expected_sha256":expected,
        "exit_code":exit_code,
        "sports_heartbeat_before":hb_before,
        "sports_heartbeat_after":hb_after,
        "stdout_tail":_tail(out),
        "stderr_tail":_tail(err),
        "startup_excerpt":_startup_excerpt(src),
        "wrapper_used":False,
        "launcher_modified":False,
        "execution_authority":False,
    }

    state=base/STATE_REL
    state.parent.mkdir(parents=True,exist_ok=True)
    result["state_path"]=str(state)
    state.write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
