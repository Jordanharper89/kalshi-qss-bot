from pathlib import Path
import json,os,time
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live

PREDICTION_LEDGER_NAME="opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME_LEDGER_NAME="opd_full_evidence_live_outcome_ledger.jsonl"
OUTCOME_LEDGER_REVISION="FULL_EVIDENCE_EXACT_FUTURE_OUTCOME_V1"
execution_authority=False
publication_allowed=False

def _load_jsonl(path):
    if not path.exists(): return []
    rows=[]
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try: rows.append(json.loads(line))
            except Exception: pass
    return rows

def _state(p):
    return {
      "state_id":p["prediction_id"],
      "anchor_id":p.get("anchor_id"),
      "anchor_sequence_boundary":int(p["anchor_sequence_boundary"]),
      "anchor_sequence_basis":"EXACT_FROZEN_PREDICTION_ANCHOR",
      "ticker":p["ticker"],
      "observed_epoch":float(p["anchor_observed_epoch"]),
      "horizon_seconds":int(p["horizon_seconds"]),
      "anchor_price":float(p["anchor_price"]),
    }

def _append(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        f.flush();os.fsync(f.fileno())

def resolve_matured(root=None,now=None,materializer=materialize_live):
    root=Path(root or Path.cwd()).resolve()
    now=float(time.time() if now is None else now)
    base=root/"runtime"/"predictive_data"
    predictions=_load_jsonl(base/PREDICTION_LEDGER_NAME)
    outcome_path=base/OUTCOME_LEDGER_NAME
    prior=_load_jsonl(outcome_path)
    done={str(x.get("prediction_id")) for x in prior if x.get("prediction_id")}
    stats={"predictions":len(predictions),"due":0,"resolved_now":0,
           "ineligible":0,"not_ready":0,"unresolved_due":0,"errors":0,
           "outcome_ledger":str(outcome_path)}
    for p in predictions:
        pid=str(p.get("prediction_id") or "")
        if not pid or pid in done: continue
        if now < float(p["resolution_due_epoch"]):
            stats["not_ready"]+=1;continue
        stats["due"]+=1
        if not bool(p.get("horizon_eligible")):
            _append(outcome_path,{
              "prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
              "generation":int(p.get("generation") or 2),"family_id":p.get("family_id"),
              "model_basis":p.get("model_basis"),
              "resolution_status":"CONTRACT_HORIZON_INELIGIBLE",
              "resolved_epoch":now,"ticker":p["ticker"],
              "horizon_seconds":int(p["horizon_seconds"]),
              "actionable_at_freeze":bool(p.get("actionable_at_freeze")),
              "execution_authority":False,"publication_allowed":False})
            done.add(pid);stats["ineligible"]+=1;continue
        try:
            out=materializer(_state(p),root,after_sequence=int(p["anchor_sequence_boundary"]))
        except Exception:
            stats["errors"]+=1;continue
        if out is None:
            stats["unresolved_due"]+=1;continue
        fr=float(out["future_return"])
        direction=str(p.get("direction") or "")
        directional_return=fr if direction=="UP" else (-fr if direction=="DOWN" else 0.0)
        _append(outcome_path,{
          "prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
          "generation":int(p.get("generation") or 2),"family_id":p.get("family_id"),
          "model_basis":p.get("model_basis"),
          "resolution_status":"RESOLVED_EXACT_FUTURE",
          "resolved_epoch":now,"ticker":p["ticker"],
          "anchor_sequence_boundary":int(p["anchor_sequence_boundary"]),
          "anchor_observed_epoch":float(p["anchor_observed_epoch"]),
          "horizon_seconds":int(p["horizon_seconds"]),
          "resolution_due_epoch":float(p["resolution_due_epoch"]),
          "direction":direction,
          "predicted_probability":p.get("predicted_probability"),
          "expected_return":p.get("expected_return"),
          "net_edge_after_2pct":p.get("net_edge_after_2pct"),
          "actionable_at_freeze":bool(p.get("actionable_at_freeze")),
          "decision_at_freeze":p.get("decision_at_freeze"),
          "future_return":fr,"directional_return":directional_return,
          "future_end_price":out.get("future_end_price"),
          "mfe":out.get("mfe"),"mae":out.get("mae"),
          "outcome_basis":out.get("outcome_basis"),
          "coverage_witness_epoch":out.get("coverage_witness_epoch"),
          "coverage_start_sequence":out.get("coverage_start_sequence"),
          "coverage_highwater_sequence":out.get("coverage_highwater_sequence"),
          "anchor_sequence_exact":bool(out.get("anchor_sequence_exact")),
          "execution_authority":False,"publication_allowed":False})
        done.add(pid);stats["resolved_now"]+=1
    return stats

def run(root=None,now=None):
    r=resolve_matured(root,now)
    print("[EXACT FUTURE RESOLVER] predictions={predictions} due={due} resolved_now={resolved_now} ineligible={ineligible} not_ready={not_ready} unresolved_due={unresolved_due} errors={errors}".format(**r),flush=True)
    print("[OUTCOME LEDGER]",r["outcome_ledger"],flush=True)
    print("[EXECUTION/PUBLICATION] FALSE/FALSE",flush=True)
    return r

if __name__=="__main__":
    run()
