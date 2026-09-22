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
