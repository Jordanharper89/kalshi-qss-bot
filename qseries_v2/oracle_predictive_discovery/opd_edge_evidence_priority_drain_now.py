from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact,mature_exact
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact
from qseries_v2.oracle_predictive_data.opd_034_prospective_oos_metrics import build as build034
from qseries_v2.oracle_predictive_data.opd_035_prospective_edge_certification_gate import build as build035
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _priority(state,candidate_horizons):
    return (0 if state.get("matched_family_ids") else 1,
            0 if int(state["horizon_seconds"]) in candidate_horizons else 1,
            float(state["maturity_epoch"]),state["state_id"])

def drain(root=None,target_resolved=512,max_attempts=1200):
    root=Path(root or Path.cwd()).resolve();rt=root/"runtime"/"predictive_data"
    freeze=json.loads((rt/"opd_031_prospective_candidate_freeze.json").read_text(encoding="utf-8"))
    candidate_horizons={int(x["horizon_seconds"]) for x in freeze["candidates"]}
    rebuild_exact(root);rows=mature_exact(root)
    rows=sorted(rows,key=lambda x:_priority(x,candidate_horizons))
    attempted=resolved=abstained=errors=trigger_resolved=0
    print("="*92);print("ORACLE PRIORITY PROSPECTIVE EDGE-EVIDENCE DRAIN");print("="*92)
    print("MATURE_AVAILABLE=",len(rows));print("TARGET_RESOLVED=",target_resolved)
    print("CANDIDATE_HORIZONS=",sorted(candidate_horizons))
    for state in rows[:int(max_attempts)]:
        if resolved>=int(target_resolved):break
        attempted+=1
        try:
            outcome=materialize_live(state,root)
            if outcome is None:
                abstained+=1;continue
            resolve_exact(outcome,root);resolved+=1
            if state.get("matched_family_ids"):trigger_resolved+=1
        except Exception as exc:
            errors+=1
            if errors<=5:print("[ERROR]",state["state_id"][:12],type(exc).__name__,str(exc))
        if attempted%25==0:
            print("[PROGRESS] attempted=",attempted,"resolved=",resolved,
                  "trigger_resolved=",trigger_resolved,"abstained=",abstained,"errors=",errors)
    s34,_=build034(root);s35,_=build035(root)
    evals=json.loads((rt/"opd_035_prospective_edge_evaluation_registry.json").read_text(encoding="utf-8"))
    print("="*92)
    print("ATTEMPTED=",attempted);print("RESOLVED_THIS_RUN=",resolved)
    print("TRIGGER_STATES_RESOLVED_THIS_RUN=",trigger_resolved)
    print("ABSTAINED=",abstained);print("ERRORS=",errors)
    print("TOTAL_RESOLVED_PROSPECTIVE_STATES=",s34["resolved_states"])
    print("CERTIFIED_EDGES=",s35["certified_edges"]);print("STATUS=",s35["status"])
    for x in evals:
        print("-"*92);print("FAMILY_ID=",x["family_id"]);print("TARGET=",x["target"])
        print("HORIZON_SECONDS=",x["horizon_seconds"]);print("BASELINE_N=",x["baseline_n"])
        print("TRIGGER_N=",x["trigger_n"]);print("TRIGGER_TICKERS=",x["trigger_tickers"])
        print("PROSPECTIVE_LIFT=",x["prospective_lift"]);print("Q_VALUE=",x["q_value"])
        print("NET_EXPECTED_AFTER_HURDLE=",x["net_expected_after_hurdle"])
        print("REWARD_RISK_PROXY=",x["reward_risk_proxy"])
        print("CERTIFIED_EDGE=",x["certified_edge"])
        print("FAILED_CHECKS=",",".join(k for k,v in x["prospective_checks"].items() if not v) or "NONE")
    print("EXECUTION_AUTHORITY=FALSE")
    return {"attempted":attempted,"resolved":resolved,"trigger_resolved":trigger_resolved,
            "abstained":abstained,"errors":errors,"opd034":s34,"opd035":s35}

if __name__=="__main__":
    drain()
