from pathlib import Path
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"; STATE=PKG/"state"
MOD=PKG/"pre_freeze_gate.py"; TEST=ROOT/"test_ksem_075_pre_freeze_production_boundary_gate.py"
MODULE=r"""
from pathlib import Path
import json
def evaluate(root=None):
    root=Path(root or Path.cwd()).resolve()
    s=root/"qseries_v2/kalshi_sports_evidence_mapping/state"
    live=json.loads((s/"ksem_live_mapping_state.json").read_text(encoding="utf-8"))
    ready=json.loads((s/"ksem070_24x7_activation_readiness.json").read_text(encoding="utf-8"))
    audit=json.loads((s/"ksem074_launcher_audit.json").read_text(encoding="utf-8"))
    heartbeat=json.loads((s/"ksem_worker_heartbeat.json").read_text(encoding="utf-8"))
    return {
        "mapping_ready":bool(ready.get("ready_for_24x7_activation")),
        "full_accounting":live.get("total_rows")==live.get("accounted_rows") and live.get("total_rows",0)>0,
        "exact_bound_count":int(live.get("counts",{}).get("EXACT_BOUND",0)),
        "worker_heartbeat":bool(heartbeat.get("completed_at")),
        "launcher_surface_audited":bool(audit.get("contains_children") and audit.get("contains_popen")),
        "launcher_already_contains_ksem":bool(audit.get("contains_ksem")),
        "execution_authority":False,
        "probability_enabled":False,
    }
"""
TEST_BODY=r"""
from pathlib import Path
import json
from qseries_v2.kalshi_sports_evidence_mapping.pre_freeze_gate import evaluate
root=Path.cwd(); r=evaluate(root); print("[GATE]",r)
assert r["mapping_ready"] and r["full_accounting"] and r["exact_bound_count"]>0
assert r["worker_heartbeat"] and r["launcher_surface_audited"]
assert r["execution_authority"] is False and r["probability_enabled"] is False
(root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem075_pre_freeze_gate.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
print("[PASS] KSEM worker/recovery/mapping boundary ready for exact launcher cutover")
print("[PASS] KSEM-075 certified as PRE-FREEZE gate; subsystem is NOT frozen until native launcher cutover is physically certified")
"""
def main():
    print("="*120); print(" KSEM-075 PRE-FREEZE PRODUCTION BOUNDARY GATE INSTALLER"); print("="*120)
    for name in ("ksem070_24x7_activation_readiness.json","ksem074_launcher_audit.json","ksem_worker_heartbeat.json","ksem_live_mapping_state.json"):
        if not (STATE/name).is_file(): raise RuntimeError(f"missing physical state: {name}")
        print("[PASS] state verified:",name)
    MOD.write_text(MODULE.lstrip(),encoding="utf-8"); TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",MOD.relative_to(ROOT)); print("[PASS] wrote",TEST.name)
    print("[PASS] this gate refuses to falsely freeze KSEM before exact launcher cutover")
    print("[PASS] KSEM-075 installer complete")
if __name__=="__main__": main()