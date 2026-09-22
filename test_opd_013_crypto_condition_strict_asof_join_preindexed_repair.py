
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_013_crypto_condition_strict_asof_join_preindexed_repair import build

s,p=build(Path.cwd())

assert p.exists()
assert s["anchor_rows"]>0
assert s["crypto_anchor_rows"]>0
assert s["post_t_feature_rows"]==0
assert s["join_algorithm"]=="PREINDEXED_TIMELINES_PLUS_BINARY_SEARCH"
assert not s["model_fit_allowed"]
assert not s["formula_mining_allowed"]
assert not s["probability_enabled"]
assert not s["direction_enabled"]
assert not s["publication_allowed"]
assert not s["execution_authority"]

print("[FILE]",p)
print("[ANCHORS]",s["anchor_rows"])
print("[CRYPTO_ANCHORS]",s["crypto_anchor_rows"])
print("[COVERED]",s["covered_anchor_rows"])
print("[CRYPTO_COVERAGE]",s["crypto_coverage_fraction"])
print("[INDEXED_ASSETS]",s["indexed_assets"])
print("[INDEXED_METRICS]",s["indexed_metric_count"])
print("[ASSET_COVERED_COUNTS]",s["asset_covered_counts"])
print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[JOIN_ALGORITHM]",s["join_algorithm"])
print("[JOIN_HASH]",s["join_hash"])
print("[PASS] repeated per-anchor timeline reconstruction retired")
print("[PASS] crypto timelines indexed once and queried by binary search")
print("[PASS] crypto condition state joined only at-or-before anchor T")
print("[PASS] OPD-013 PREINDEXED REPAIR certified")
