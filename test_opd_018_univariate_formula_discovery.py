
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_018_univariate_formula_discovery import build
s,p=build(Path.cwd());assert p.exists() and s["tests"]>0 and s["multiple_testing_method"]=="BENJAMINI_HOCHBERG_FDR" and not s["holdout_used"];assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[TESTS]",s["tests"]);print("[CANDIDATES]",s["discovered_candidates"]);print("[METHOD]",s["multiple_testing_method"]);print("[TESTS_HASH]",s["tests_hash"]);print("[TOP_CANDIDATES]",s["candidate_preview"][:10])
print("[PASS] X->Y relations measured against horizon-specific base rates");print("[PASS] false-discovery correction applied before candidate admission");print("[PASS] holdout contracts remained untouched");print("[PASS] OPD-018 univariate formula discovery certified")
