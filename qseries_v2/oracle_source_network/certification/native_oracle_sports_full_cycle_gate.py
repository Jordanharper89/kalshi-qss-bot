from pathlib import Path
import subprocess,sys,time,json,hashlib,os,threading,queue,re

S094=Path("qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json")
HB=Path("qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json")
STATE=Path("qseries_v2/oracle_source_network/state/osn095_native_sports_full_cycle_gate.json")
LEAGUES=("NFL","NCAAF","NBA","NHL","MLS","EPL")

def _j(p):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {}

def _reader(stream,q):
    for line in iter(stream.readline,""):
        if not line:break
        q.put(line.rstrip())

def run_gate(root=None,timeout_seconds=210.0):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    s094=_j(root/S094)
    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()
    if actual!=s094.get("post_patch_sha256"):
        raise RuntimeError("launcher hash differs from certified OSN-094 image")

    before=_j(root/HB)
    c0=int(before.get("cycles",0) or 0)
    stamp0=before.get("last_heartbeat")

    env=os.environ.copy();env["PYTHONUNBUFFERED"]="1"
    p=subprocess.Popen([sys.executable,str(launcher),"--cadence-seconds","2"],
        cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,bufsize=1,env=env)
    q=queue.Queue()
    threading.Thread(target=_reader,args=(p.stdout,q),daemon=True).start()

    lines=[]; seen=set(); oracle_healthy=False; sports_restarts=None
    deadline=time.time()+timeout_seconds
    try:
        while time.time()<deadline:
            while True:
                try: line=q.get_nowait()
                except queue.Empty: break
                lines.append(line)
                if "[ORACLE]" in line and "sports=HEALTHY" in line:
                    oracle_healthy=True
                    m=re.search(r"sports_restarts=(\d+)",line)
                    if m:sports_restarts=int(m.group(1))
                if "[RUNTIME_CYCLE]" in line:
                    for lg in LEAGUES:
                        if "league='"+lg+"'" in line:
                            seen.add(lg)

            if p.poll() is not None:
                raise RuntimeError("run_oracle_LIVE.py exited\nOUTPUT:\n"+"\n".join(lines[-250:]))

            cur=_j(root/HB)
            c1=int(cur.get("cycles",0) or 0)
            stamp1=cur.get("last_heartbeat")
            advanced=(c1>=c0+1 and stamp1 and stamp1!=stamp0)

            if oracle_healthy and set(LEAGUES).issubset(seen) and advanced:
                result={
                    "launcher":"run_oracle_LIVE.py",
                    "launcher_sha256":actual,
                    "launcher_process_alive":p.poll() is None,
                    "oracle_reported_sports_healthy":True,
                    "leagues_seen":sorted(seen),
                    "all_six_leagues_seen":True,
                    "sports_cycles_start":c0,
                    "sports_cycles_end":c1,
                    "sports_heartbeat_advanced":True,
                    "sports_restarts":sports_restarts if sports_restarts is not None else 0,
                    "wrapper_used":False,
                    "terminal_dependency":"NONE",
                    "execution_authority":False,
                    "oracle_output_tail":lines[-120:]
                }
                out=root/STATE;out.parent.mkdir(parents=True,exist_ok=True)
                out.write_text(json.dumps(result,indent=2),encoding="utf-8")
                return result
            time.sleep(.5)

        cur=_j(root/HB)
        raise RuntimeError(
            "full sports cycle did not finish inside bounded 210s gate; "
            f"leagues_seen={sorted(seen)} heartbeat_before={c0} heartbeat_after={cur.get('cycles')} "
            f"oracle_sports_healthy={oracle_healthy}\nOUTPUT:\n"+"\n".join(lines[-250:])
        )
    finally:
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=20)
            except Exception:
                p.kill()
                try:p.wait(timeout=5)
                except Exception:pass
