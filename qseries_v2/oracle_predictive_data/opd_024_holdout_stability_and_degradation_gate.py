
from pathlib import Path
import hashlib,json
MIN_HOLDOUT_N=60;MIN_HOLDOUT_TICKERS=5;MIN_LIFT_RETENTION=0.25;MAX_Q=0.10
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";rows=json.loads((rt/"opd_023_frozen_formula_holdout_scores.json").read_text())
    outrows=[]
    for x in rows:
        lift=x.get("holdout_lift");ret=x.get("lift_retention")
        checks={"min_holdout_n":x["holdout_n"]>=MIN_HOLDOUT_N,"min_holdout_tickers":x["holdout_ticker_count"]>=MIN_HOLDOUT_TICKERS,
                "sign_preserved":bool(x["sign_preserved"]),"fdr_q_le_010":x["q_value"]<=MAX_Q,
                "lift_retention_ge_025":ret is not None and ret>=MIN_LIFT_RETENTION}
        status="HOLDOUT_SURVIVOR" if all(checks.values()) else "REJECTED_OR_OBSERVE"
        z=dict(x);z["validation_checks"]=checks;z["validation_status"]=status;outrows.append(z)
    surv=[x for x in outrows if x["validation_status"]=="HOLDOUT_SURVIVOR"]
    vals=sorted([x["lift_retention"] for x in outrows if x.get("lift_retention") is not None])
    rf=rt/"opd_024_holdout_stability_and_degradation_registry.json";rf.write_text(json.dumps(outrows,indent=2,sort_keys=True))
    s={"schema_version":"OPD-024","fixed_thresholds":{"min_holdout_n":MIN_HOLDOUT_N,"min_holdout_tickers":MIN_HOLDOUT_TICKERS,"min_lift_retention":MIN_LIFT_RETENTION,"max_q":MAX_Q},
       "families_evaluated":len(outrows),"holdout_survivors":len(surv),"rejected_or_observe":len(outrows)-len(surv),
       "median_retention":vals[len(vals)//2] if vals else None,"thresholds_tuned_on_holdout":False,
       "registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0,
       "model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_024_holdout_stability_and_degradation_gate.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
