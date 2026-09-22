from pathlib import Path
import importlib.util,sys,json,time
root=Path.cwd()
name="oracle_live_ksem078_py314"
spec=importlib.util.spec_from_file_location(name,root/"run_oracle_LIVE.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[name]=mod
spec.loader.exec_module(mod)
assert mod.CHILDREN.get("ksem_mapping")=="run_ksem_live_mapping.py"
hb=root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json"
before=json.loads(hb.read_text()) if hb.is_file() else {}
before_completed=before.get("completed_at")
proc=mod._start(root,mod.CHILDREN["ksem_mapping"])
try:
    deadline=time.time()+90; fresh=None
    while time.time()<deadline:
        if proc.poll() is not None: raise RuntimeError(f"KSEM_CHILD_EXITED code={proc.returncode}")
        if hb.is_file():
            cur=json.loads(hb.read_text())
            if cur.get("completed_at") and cur.get("completed_at")!=before_completed:
                fresh=cur; break
        time.sleep(1)
    assert fresh is not None,"native launcher child did not advance KSEM heartbeat within 90s"
    print("[HEARTBEAT]",fresh)
    assert fresh["accounted_rows"]==fresh["total_rows"]>0
    assert fresh["execution_authority"] is False and fresh["probability_enabled"] is False
finally:
    proc.terminate()
    try: proc.wait(timeout=10)
    except Exception: proc.kill()
print("[PASS] Python 3.14-safe dynamic launcher import verified")
print("[PASS] run_oracle_LIVE._start physically launched KSEM child and durable state advanced")
print("[PASS] KSEM-078 certified")
