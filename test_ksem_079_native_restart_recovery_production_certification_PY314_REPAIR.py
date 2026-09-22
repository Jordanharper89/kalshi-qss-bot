from pathlib import Path
import importlib.util,sys,json,time
root=Path.cwd()
name="oracle_live_ksem079_py314"
spec=importlib.util.spec_from_file_location(name,root/"run_oracle_LIVE.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[name]=mod
spec.loader.exec_module(mod)
runner=mod.CHILDREN["ksem_mapping"]
hb=root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json"
def snap(): return json.loads(hb.read_text()) if hb.is_file() else {}
def start_and_wait(previous,timeout=90):
    p=mod._start(root,runner)
    try:
        deadline=time.time()+timeout
        while time.time()<deadline:
            if p.poll() is not None: raise RuntimeError(f"KSEM_CHILD_EXITED code={p.returncode}")
            cur=snap()
            if cur.get("completed_at") and cur.get("completed_at")!=previous: return p,cur
            time.sleep(1)
        raise RuntimeError("KSEM_HEARTBEAT_DID_NOT_ADVANCE")
    except Exception:
        p.terminate()
        raise
p1,a=start_and_wait(snap().get("completed_at")); print("[FIRST]",a)
p1.terminate(); p1.wait(timeout=10)
p2,b=start_and_wait(a.get("completed_at")); print("[RESTART]",b)
p2.terminate(); p2.wait(timeout=10)
assert a["accounted_rows"]==a["total_rows"]>0
assert b["accounted_rows"]==b["total_rows"]>0
assert b["completed_at"]!=a["completed_at"]
assert a["execution_authority"] is False and b["execution_authority"] is False
recovery=json.loads((root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_restart_recovery.json").read_text())
print("[RECOVERY]",recovery)
assert recovery["recovered_prior_state"] is True
assert recovery["resumed_total_rows"]==recovery["resumed_accounted_rows"]>0
print("[PASS] Python 3.14-safe native launcher import verified")
print("[PASS] native launcher child restarted, recovered checkpoint, and advanced again")
print("[PASS] KSEM-079 certified")
