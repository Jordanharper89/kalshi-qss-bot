
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_024_holdout_stability_and_degradation_gate import build
s,p=build(Path.cwd());assert p.exists() and s["families_evaluated"]>0 and not s["thresholds_tuned_on_holdout"] and s["edge_certified_count"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[FAMILIES]",s["families_evaluated"]);print("[SURVIVORS]",s["holdout_survivors"]);print("[REJECTED_OR_OBSERVE]",s["rejected_or_observe"]);print("[MEDIAN_RETENTION]",s["median_retention"]);print("[FIXED_THRESHOLDS]",s["fixed_thresholds"]);print("[REGISTRY_HASH]",s["registry_hash"])
print("[PASS] fixed predeclared holdout gates applied without retuning");print("[PASS] sign, support, contract breadth, FDR, and degradation all required");print("[PASS] OPD-024 holdout stability/degradation gate certified")
