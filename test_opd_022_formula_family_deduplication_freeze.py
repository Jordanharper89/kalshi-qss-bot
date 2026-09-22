
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_022_formula_family_deduplication_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["family_count"]>0 and s["family_count"]<=s["input_candidates"] and not s["holdout_used"] and s["edge_certified_count"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[INPUT_CANDIDATES]",s["input_candidates"]);print("[FAMILIES]",s["family_count"]);print("[COLLAPSED_DUPLICATES]",s["collapsed_duplicates"]);print("[MAX_FAMILY_SIZE]",s["max_family_size"]);print("[DEGREE_COUNTS]",s["degree_counts"]);print("[FAMILY_HASH]",s["family_hash"])
print("[PASS] discovery candidates collapsed into exact-statistic equivalence families before holdout scoring");print("[PASS] no holdout information influenced family construction");print("[PASS] OPD-022 formula-family deduplication freeze certified")
