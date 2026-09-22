
from pathlib import Path
from collections import Counter
import hashlib,json
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";rows=json.loads((rt/"opd_029_transaction_hurdle_path_quality_registry.json").read_text());cand=[]
    for x in rows:
        if not x.get("economic_gate_pass"):continue
        cand.append({"family_id":x["family_id"],"representative_formula_id":x["representative_formula_id"],"degree":x["degree"],"horizon_seconds":x["horizon_seconds"],"target":x["target"],"formula":x["formula"],"discovery_n":x["discovery_n"],"discovery_lift":x["discovery_lift"],"holdout_n":x["holdout_n"],"holdout_ticker_count":x["holdout_ticker_count"],"holdout_lift":x["holdout_lift"],"lift_retention":x["lift_retention"],"holdout_q_value":x["holdout_q_value"],"aligned_segments":x["aligned_segments"],"ticker_count":x["ticker_count"],"aligned_ticker_rate":x["aligned_ticker_rate"],"overlap_cluster_size":x["overlap_cluster_size"],"net_expected_after_hurdle":x["net_expected_after_hurdle"],"reward_risk_proxy":x["reward_risk_proxy"],"status":"EDGE_CANDIDATE","edge_certified":False,"prospective_oos_required":True})
    cand.sort(key=lambda x:(-x["net_expected_after_hurdle"],x["holdout_q_value"],-x["holdout_n"]))
    rf=rt/"opd_030_edge_candidate_registry.json";rf.write_text(json.dumps(cand,indent=2,sort_keys=True))
    s={"schema_version":"OPD-030","edge_candidates":len(cand),"degree_counts":dict(Counter(str(x["degree"]) for x in cand)),"edge_certified_count":0,"edge_claim_allowed":False,"historical_secondary_oos_available":False,"next_required":"PROSPECTIVE_LIVE_OOS_OBSERVATION_WITH_FROZEN_FORMULAS_AND_NO_RETUNING","registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_030_edge_candidate_registry_freeze.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
