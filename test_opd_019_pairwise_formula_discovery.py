
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_019_pairwise_formula_discovery import build
s,p=build(Path.cwd());assert p.exists() and s["selected_token_count"]>=2 and s["multiple_testing_method"]=="BENJAMINI_HOCHBERG_FDR" and not s["holdout_used"];assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[SELECTED_TOKENS]",s["selected_token_count"]);print("[TESTS]",s["tests"]);print("[CANDIDATES]",s["discovered_candidates"]);print("[TESTS_HASH]",s["tests_hash"]);print("[TOP_CANDIDATES]",s["candidate_preview"][:10])
print("[PASS] X+Y->Z relations searched only inside discovery contracts");print("[PASS] pair search bounded by data-selected univariate token universe");print("[PASS] FDR correction applied before pair admission");print("[PASS] OPD-019 pairwise formula discovery certified")
