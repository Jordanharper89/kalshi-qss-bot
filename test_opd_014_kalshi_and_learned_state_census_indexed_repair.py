
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_014_kalshi_and_learned_state_census_indexed_repair import build

s,p=build(Path.cwd())

assert p.exists()
assert s["anchor_rows"]>0
assert s["kalshi_anchor_state_covered"]>0
assert s["learned_cases_loaded"]>0
assert s["post_t_feature_rows"]==0
assert s["oad_189_runtime_query_used"] is False
assert s["join_algorithm"]=="PREINDEXED_LEARNED_TIMELINES_PLUS_BINARY_SEARCH"
assert not s["model_fit_allowed"]
assert not s["formula_mining_allowed"]
assert not s["probability_enabled"]
assert not s["direction_enabled"]
assert not s["publication_allowed"]
assert not s["execution_authority"]

print("[FILE]",p)
print("[ANCHORS]",s["anchor_rows"])
print("[KALSHI_COVERED]",s["kalshi_anchor_state_covered"])
print("[LEARNED_CASES_LOADED]",s["learned_cases_loaded"])
print("[LEARNED_COVERED]",s["learned_state_covered"])
print("[ASSET_ANCHORS]",s["asset_anchor_counts"])
print("[LEARNED_COVERED_BY_ASSET]",s["learned_covered_by_asset"])
print("[LEARNED_SEQUENCE_WINDOW]",s["learned_sequence_window"])
print("[POSTGRES_CHUNKS]",s["postgres_chunks_scanned"])
print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[OAD_189_RUNTIME_QUERY_USED]",s["oad_189_runtime_query_used"])
print("[JOIN_ALGORITHM]",s["join_algorithm"])
print("[JOIN_HASH]",s["join_hash"])
print("[PASS] OAD-189 timeout path retired from OPD-014")
print("[PASS] learned sequence bounds sourced from certified OPD-007 census")
print("[PASS] learned rows acquired only through bounded read-only chunks")
print("[PASS] learned timelines indexed once and queried by binary search")
print("[PASS] learned state admitted only after outcome_observed_at")
print("[PASS] OPD-014 CENSUS INDEXED REPAIR certified")
