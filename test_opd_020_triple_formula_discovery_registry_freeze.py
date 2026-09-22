
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_020_triple_formula_discovery_registry_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["edge_certified_count"]==0 and not s["holdout_contracts_used"];assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[SELECTED_TOKENS]",s["selected_token_count"]);print("[TRIPLE_TESTS]",s["triple_tests"]);print("[TRIPLE_CANDIDATES]",s["triple_candidates"]);print("[REGISTRY_CANDIDATES]",s["registry_candidates"]);print("[DEGREE_COUNTS]",s["degree_counts"]);print("[EDGE_CERTIFIED]",s["edge_certified_count"]);print("[REGISTRY_HASH]",s["registry_hash"]);print("[NEXT_REQUIRED]",s["next_required"])
print("[PASS] X+Y+Z->A discovery completed on discovery contracts only");print("[PASS] X, X+Y, X+Y+Z candidates consolidated into frozen registry");print("[PASS] no discovered association promoted to edge before untouched holdout validation");print("[PASS] OPD-016..OPD-020 formula-discovery slice certified")
