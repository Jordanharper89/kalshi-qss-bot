from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_025_validated_association_registry_freeze.py";TEST=ROOT/"test_opd_025_validated_association_registry_freeze.py"
MOD.write_text(r"""
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
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_025_validated_association_registry_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["edge_certified_count"]==0 and not s["edge_claim_allowed"]
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[VALIDATED_ASSOCIATIONS]",s["validated_associations"]);print("[DEGREE_COUNTS]",s["degree_counts"]);print("[EDGE_CERTIFIED]",s["edge_certified_count"]);print("[NEXT_REQUIRED]",s["next_required"]);print("[REGISTRY_HASH]",s["registry_hash"])
print("[PASS] only holdout survivors entered validated-association registry");print("[PASS] validated association remains distinct from certified tradable edge");print("[PASS] OPD-021..OPD-025 ruthless holdout-validation slice certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-025 installer complete")