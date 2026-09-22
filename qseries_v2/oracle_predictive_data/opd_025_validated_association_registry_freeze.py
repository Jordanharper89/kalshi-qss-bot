
from pathlib import Path
from collections import Counter
import hashlib,json
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";rows=json.loads((rt/"opd_024_holdout_stability_and_degradation_registry.json").read_text())
    survivors=[]
    for x in rows:
        if x["validation_status"]!="HOLDOUT_SURVIVOR":continue
        survivors.append({"family_id":x["family_id"],"representative_formula_id":x["representative_formula_id"],"degree":x["degree"],
                          "horizon_seconds":x["horizon_seconds"],"target":x["target"],"formula":x["formula"],
                          "discovery_n":x["discovery_n"],"discovery_lift":x["discovery_lift"],"holdout_n":x["holdout_n"],
                          "holdout_ticker_count":x["holdout_ticker_count"],"holdout_lift":x["holdout_lift"],"lift_retention":x["lift_retention"],
                          "holdout_q_value":x["q_value"],"status":"VALIDATED_ASSOCIATION","edge_certified":False,
                          "next_required":"TEMPORAL_OR_SECONDARY_OOS_PLUS_TRANSACTION_HURDLE"})
    survivors.sort(key=lambda x:(x["holdout_q_value"],-abs(x["holdout_lift"]),-x["holdout_n"]))
    rf=rt/"opd_025_validated_association_registry.json";rf.write_text(json.dumps(survivors,indent=2,sort_keys=True))
    s={"schema_version":"OPD-025","validated_associations":len(survivors),"degree_counts":dict(Counter(str(x["degree"]) for x in survivors)),
       "edge_certified_count":0,"edge_claim_allowed":False,"next_required":"SECONDARY_OOS_TEMPORAL_VALIDATION_AND_TRANSACTION_HURDLE",
       "registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"model_fit_allowed":False,"formula_mining_allowed":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_025_validated_association_registry_freeze.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
