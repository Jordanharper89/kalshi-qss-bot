
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_025_validated_association_registry_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["edge_certified_count"]==0 and not s["edge_claim_allowed"]
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[VALIDATED_ASSOCIATIONS]",s["validated_associations"]);print("[DEGREE_COUNTS]",s["degree_counts"]);print("[EDGE_CERTIFIED]",s["edge_certified_count"]);print("[NEXT_REQUIRED]",s["next_required"]);print("[REGISTRY_HASH]",s["registry_hash"])
print("[PASS] only holdout survivors entered validated-association registry");print("[PASS] validated association remains distinct from certified tradable edge");print("[PASS] OPD-021..OPD-025 ruthless holdout-validation slice certified")
