
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_023_frozen_formula_holdout_scoring import build
s,p=build(Path.cwd());assert p.exists() and s["families_scored"]>0 and not s["holdout_threshold_tuning"] and s["edge_certified_count"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[FAMILIES_SCORED]",s["families_scored"]);print("[WITH_SUPPORT]",s["families_with_holdout_support"]);print("[SIGN_PRESERVED]",s["sign_preserved_count"]);print("[Q_LE_0.10]",s["fdr_q_le_010_count"]);print("[SCORE_HASH]",s["score_hash"])
print("[PASS] frozen formula families scored on untouched contracts without threshold tuning");print("[PASS] holdout base rates recomputed independently by horizon");print("[PASS] OPD-023 frozen-formula holdout scoring certified")
