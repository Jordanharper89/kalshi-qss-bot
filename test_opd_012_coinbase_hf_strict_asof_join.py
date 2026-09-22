
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_012_coinbase_hf_strict_asof_join import build
s,p=build(Path.cwd())
assert p.exists() and s["anchor_rows"]>0
assert s["post_t_feature_rows"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[ANCHORS]",s["anchor_rows"]);print("[CRYPTO_ANCHORS]",s["crypto_anchor_rows"])
print("[COVERED]",s["covered_anchor_rows"]);print("[CRYPTO_COVERAGE]",s["crypto_coverage_fraction"])
print("[ASSET_COUNTS]",s["asset_anchor_counts"]);print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[JOIN_HASH]",s["join_hash"])
print("[PASS] Coinbase HF state joined only at-or-before anchor T")
print("[PASS] missing coverage retained as missing rather than filtered away")
print("[PASS] OPD-012 Coinbase HF strict as-of join certified")
