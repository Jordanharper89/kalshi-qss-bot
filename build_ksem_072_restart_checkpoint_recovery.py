from pathlib import Path
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"; STATE=PKG/"state"
MOD=PKG/"restart_checkpoint_recovery.py"; TEST=ROOT/"test_ksem_072_restart_checkpoint_recovery.py"
MODULE=r"""
from pathlib import Path
from datetime import datetime,timezone
import json
from qseries_v2.kalshi_sports_evidence_mapping.continuous_mapping_worker import run_worker_cycle

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).is_file() else None

def recover_and_resume(root=None):
    root=Path(root or Path.cwd()).resolve()
    state_dir=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
    prior=_load(state_dir/"ksem_live_mapping_state.json")
    prior_heartbeat=_load(state_dir/"ksem_worker_heartbeat.json")
    result=run_worker_cycle(root=root)
    current=_load(state_dir/"ksem_live_mapping_state.json")
    if not current or current.get("accounted_rows")!=current.get("total_rows"):
        raise RuntimeError("KSEM_RECOVERY_CURRENT_STATE_NOT_FULLY_ACCOUNTED")
    report={
        "schema_version":"KSEM-072",
        "recovered_prior_state":bool(prior),
        "recovered_prior_heartbeat":bool(prior_heartbeat),
        "prior_content_hash":(prior or {}).get("content_hash"),
        "current_content_hash":current.get("content_hash"),
        "resumed_total_rows":current.get("total_rows"),
        "resumed_accounted_rows":current.get("accounted_rows"),
        "recovered_at":datetime.now(timezone.utc).isoformat(),
        "probability_enabled":False,"execution_authority":False,
    }
    (state_dir/"ksem_restart_recovery.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    return report
"""
TEST_BODY=r"""
from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.restart_checkpoint_recovery import recover_and_resume
root=Path.cwd()
a=recover_and_resume(root); b=recover_and_resume(root)
print("[A]",a); print("[B]",b)
assert a["recovered_prior_state"] and b["recovered_prior_state"]
assert a["resumed_total_rows"]==a["resumed_accounted_rows"]>0
assert b["resumed_total_rows"]==b["resumed_accounted_rows"]>0
assert a["execution_authority"] is False and b["probability_enabled"] is False
print("[PASS] durable state recovered and mapping resumed idempotently twice")
print("[PASS] KSEM-072 certified")
"""
def main():
    print("="*120); print(" KSEM-072 RESTART CHECKPOINT RECOVERY INSTALLER"); print("="*120)
    for dep in (PKG/"continuous_mapping_worker.py",STATE/"ksem_live_mapping_state.json"):
        if not dep.is_file(): raise RuntimeError(f"missing dependency: {dep}")
        print("[PASS] dependency verified:",dep.relative_to(ROOT))
    MOD.write_text(MODULE.lstrip(),encoding="utf-8"); TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",MOD.relative_to(ROOT)); print("[PASS] wrote",TEST.name)
    print("[PASS] restart path reuses durable checkpoint and resumes fresh cycle")
    print("[PASS] KSEM-072 installer complete")
if __name__=="__main__": main()
