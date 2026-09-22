
from pathlib import Path
import hashlib,json
MIN_BASELINE_N=500;MIN_TRIGGER_N=100;MIN_TICKERS=10;MAX_Q=0.05;MIN_LIFT_RETENTION=0.25
TOTAL_HURDLE=0.020;MIN_NET_EXPECTED=0.005;MIN_FAVORABLE_EXCURSION=0.03;MIN_REWARD_RISK=1.20
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";rows=json.loads((rt/"opd_034_prospective_oos_metrics_registry.json").read_text());cert=[];evaluated=[]
    for x in rows:
        net=(x["directional_mean_return"]-TOTAL_HURDLE) if x["directional_mean_return"] is not None else None
        rr=(x["mean_favorable_excursion"]/max(x["mean_adverse_excursion"],1e-9)) if x["mean_favorable_excursion"] is not None and x["mean_adverse_excursion"] is not None else None
        checks={"baseline_n":x["baseline_n"]>=MIN_BASELINE_N,"trigger_n":x["trigger_n"]>=MIN_TRIGGER_N,"tickers":x["trigger_tickers"]>=MIN_TICKERS,
                "sign_preserved":bool(x["sign_preserved"]),"q_value":x["q_value"]<=MAX_Q,"lift_retention":x["lift_retention"] is not None and x["lift_retention"]>=MIN_LIFT_RETENTION,
                "net_expected":net is not None and net>=MIN_NET_EXPECTED,"favorable_excursion":x["mean_favorable_excursion"] is not None and x["mean_favorable_excursion"]>=MIN_FAVORABLE_EXCURSION,
                "reward_risk":rr is not None and rr>=MIN_REWARD_RISK}
        z=dict(x);z["prospective_checks"]=checks;z["net_expected_after_hurdle"]=net;z["reward_risk_proxy"]=rr;z["certified_edge"]=all(checks.values());evaluated.append(z)
        if z["certified_edge"]:cert.append({"family_id":z["family_id"],"horizon_seconds":z["horizon_seconds"],"target":z["target"],"status":"CERTIFIED_EDGE","prospective_trigger_n":z["trigger_n"],"prospective_tickers":z["trigger_tickers"],"prospective_lift":z["prospective_lift"],"prospective_q":z["q_value"],"net_expected_after_hurdle":net,"reward_risk_proxy":rr})
    ef=rt/"opd_035_prospective_edge_evaluation_registry.json";ef.write_text(json.dumps(evaluated,indent=2,sort_keys=True))
    cf=rt/"opd_035_certified_edge_registry.json";cf.write_text(json.dumps(cert,indent=2,sort_keys=True))
    s={"schema_version":"OPD-035","candidates_evaluated":len(rows),"certified_edges":len(cert),"status":"CERTIFIED_EDGES_AVAILABLE" if cert else "WAITING_FOR_PROSPECTIVE_EVIDENCE",
       "fixed_thresholds":{"min_baseline_n":MIN_BASELINE_N,"min_trigger_n":MIN_TRIGGER_N,"min_tickers":MIN_TICKERS,"max_q":MAX_Q,"min_lift_retention":MIN_LIFT_RETENTION,
       "total_hurdle":TOTAL_HURDLE,"min_net_expected":MIN_NET_EXPECTED,"min_favorable_excursion":MIN_FAVORABLE_EXCURSION,"min_reward_risk":MIN_REWARD_RISK},
       "threshold_retuning_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False,
       "certified_registry_hash":hashlib.sha256(cf.read_bytes()).hexdigest()}
    out=rt/"opd_035_prospective_edge_certification_gate.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
