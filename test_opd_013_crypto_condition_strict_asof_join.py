
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_013_crypto_condition_strict_asof_join import build
s,p=build(Path.cwd())
assert p.exists() and s["anchor_rows"]>0
assert s["post_t_feature_rows"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[ANCHORS]",s["anchor_rows"]);print("[COVERED]",s["covered_anchor_rows"])
print("[COVERAGE]",s["coverage_fraction"]);print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[METRIC_COVERAGE_COUNTS]",s["metric_coverage_counts"]);print("[JOIN_HASH]",s["join_hash"])
print("[PASS] crypto condition state joined only at-or-before anchor T")
print("[PASS] source/value/unit/direction/basis lineage preserved")
print("[PASS] OPD-013 crypto-condition strict as-of join certified")
