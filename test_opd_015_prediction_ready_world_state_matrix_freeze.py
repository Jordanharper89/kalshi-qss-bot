
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_015_prediction_ready_world_state_matrix_freeze import build
s,p=build(Path.cwd())
assert p.exists() and s["matrix_rows"]>0
assert s["zero_post_t_feature_leakage"] is True
assert s["prediction_ready_matrix_frozen"] is True
assert s["formula_mining_next"] is True
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[MATRIX_ROWS]",s["matrix_rows"]);print("[CRYPTO_ANCHORS]",s["crypto_anchor_rows"])
print("[CRYPTO_CORE_COVERED]",s["crypto_rows_with_kalshi_coinbase_conditions"])
print("[CRYPTO_CORE_COVERAGE]",s["crypto_core_coverage_fraction"])
print("[MISSING_FEATURE_COUNTS]",s["missing_feature_counts"]);print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[MATRIX_HASH]",s["matrix_hash"]);print("[NEXT_REQUIRED]",s["next_required"])
print("[PASS] state-at-T features and strictly-future targets frozen in one auditable matrix")
print("[PASS] zero post-T feature leakage certified across joined feature families")
print("[PASS] no model/formula/edge claim enabled before discovery validation")
print("[PASS] OPD-011..OPD-015 historical world-state matrix slice certified")
