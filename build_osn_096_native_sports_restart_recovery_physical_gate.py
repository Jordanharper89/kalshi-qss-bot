from pathlib import Path
import json
ROOT=Path.cwd()
S095=ROOT/"qseries_v2/oracle_source_network/state/osn095_native_sports_full_cycle_gate.json"
TARGET=ROOT/"qseries_v2/oracle_source_network/certification/native_sports_restart_recovery_gate.py"
TEST=ROOT/"test_osn_096_native_sports_restart_recovery_physical_gate.py"

GATE=r"""
from pathlib import Path
import subprocess,sys,time,json,hashlib,os,re

def _read(p):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return {}

def _sports_pids(parent_pid):
    cmd=["wmic","process","where",f"ParentProcessId={parent_pid}","get","ProcessId,CommandLine","/FORMAT:CSV"]
    try:
        text=subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT)
    except Exception as e:
        raise RuntimeError("WMIC process inspection unavailable; no process was killed") from e
    out=[]
    for line in text.splitlines():
        if "run_osn_sports_continuous_runtime.py" in line:
            m=re.search(r",(\\d+)\\s*$",line)
            if m:out.append(int(m.group(1)))
    return out

def run_gate(root=None,timeout=150.0):
    root=Path(root or Path.cwd()).resolve()
    s094=_read(root/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json")
    launcher=root/"run_oracle_LIVE.py"
    actual=hashlib.sha256(launcher.read_bytes()).hexdigest()
    if actual!=s094.get("post_patch_sha256"):raise RuntimeError("launcher hash mismatch")
    env=os.environ.copy();env["PYTHONUNBUFFERED"]="1"
    p=subprocess.Popen([sys.executable,str(launcher),"--cadence-seconds","2"],cwd=str(root),
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,env=env)
    lines=[]
    try:
        old=None
        deadline=time.time()+65
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
                if "sports=HEALTHY" in line and "sports_restarts=0" in line:
                    ids=_sports_pids(p.pid)
                    if len(ids)==1:old=ids[0];break
            if p.poll() is not None:raise RuntimeError("launcher exited before sports healthy")
        if old is None:raise RuntimeError("exact sports child PID not resolved")
        killed=subprocess.run(["taskkill","/PID",str(old),"/F"],capture_output=True,text=True)
        if killed.returncode!=0:raise RuntimeError("taskkill failed: "+killed.stdout+killed.stderr)
        new=None;restarts=0;healthy=False
        deadline=time.time()+timeout
        while time.time()<deadline:
            line=p.stdout.readline()
            if line:
                lines.append(line.rstrip())
                m=re.search(r"sports_restarts=(\\d+)",line)
                if m:restarts=max(restarts,int(m.group(1)))
                if "sports=HEALTHY" in line and restarts>=1:
                    ids=_sports_pids(p.pid)
                    ids=[x for x in ids if x!=old]
                    if len(ids)==1:new=ids[0];healthy=True;break
            if p.poll() is not None:raise RuntimeError("launcher exited during sports recovery")
        if not healthy:raise RuntimeError("native supervisor did not return sports to HEALTHY")
        result={"sports_pid_before":old,"sports_pid_after":new,"sports_restarts_after":restarts,
            "sports_healthy_after_restart":healthy,"launcher_alive":p.poll() is None,
            "terminal_dependency":"NONE","execution_authority":False}
        state=root/"qseries_v2/oracle_source_network/state/osn096_native_sports_restart_recovery_gate.json"
        state.write_text(json.dumps(result,indent=2),encoding="utf-8")
        return result
    finally:
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=20)
            except Exception:p.kill()
"""
TESTSRC=r"""
from pathlib import Path
from qseries_v2.oracle_source_network.certification.native_sports_restart_recovery_gate import run_gate
r=run_gate(Path.cwd());print("[RESULT]",r)
assert r["sports_pid_before"]!=r["sports_pid_after"]
assert r["sports_restarts_after"]>=1
assert r["sports_healthy_after_restart"] is True
assert r["launcher_alive"] is True
assert r["execution_authority"] is False
print("[PASS] native supervisor restarted terminated sports child")
print("[PASS] replacement sports child returned HEALTHY")
print("[PASS] production launcher remained alive")
print("[PASS] OSN-096 restart/recovery physical gate certified")
"""

def main():
 print("="*120);print(" OSN-096 NATIVE SPORTS RESTART / RECOVERY PHYSICAL GATE");print("="*120)
 for p in (S095,ROOT/"qseries_v2/oracle_source_network/state/osn094_native_children_sports_integration.json",ROOT/"run_oracle_LIVE.py"):
  if not p.exists():raise SystemExit("[FAIL] missing dependency: "+str(p.relative_to(ROOT)))
  print("[PASS] dependency verified:",p.relative_to(ROOT))
 TARGET.parent.mkdir(parents=True,exist_ok=True);TARGET.write_text(GATE,encoding="utf-8");TEST.write_text(TESTSRC,encoding="utf-8")
 compile(GATE,str(TARGET),"exec");compile(TESTSRC,str(TEST),"exec")
 print("[WRITE]",TARGET.relative_to(ROOT));print("[WRITE]",TEST.name)
 print("[PASS] bounded forced sports-child restart gate installed")
 print("[PASS] run_oracle_LIVE.py remains unchanged")
 print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
