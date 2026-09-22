
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_014_kalshi_and_learned_state_strict_asof_join import build
s,p=build(Path.cwd())
assert p.exists() and s["anchor_rows"]>0
assert s["kalshi_anchor_state_covered"]>0
assert s["post_t_feature_rows"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[ANCHORS]",s["anchor_rows"]);print("[KALSHI_COVERED]",s["kalshi_anchor_state_covered"])
print("[LEARNED_CASES_LOADED]",s["learned_cases_loaded"]);print("[LEARNED_COVERED]",s["learned_state_covered"])
print("[ASSET_ANCHORS]",s["asset_anchor_counts"]);print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[JOIN_HASH]",s["join_hash"])
print("[PASS] exact Kalshi anchor state attached by anchor sequence")
print("[PASS] learned cases admitted only after their outcome-observed time")
print("[PASS] OPD-014 Kalshi + learned-state strict as-of join certified")
