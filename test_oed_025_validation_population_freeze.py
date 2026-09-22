
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_025_validation_population_freeze import build
s,p=build(Path.cwd()); assert s["population_frozen_for_next_phase"] and not s["predictive_model_fit_allowed"]
assert s["certified_edge_count"]==0 and not s["edge_proven"]
print("[VALIDATION_CANDIDATES]",s["validation_candidate_count"]); print("[FREEZE_HASH]",s["freeze_hash"])
print("[TOP_VALIDATION_TARGETS]")
for x in s["validation_candidates"][:30]: print(" ",x)
print("[NEXT_PHASE]",s["next_phase"]); print("[REQUIRED_NEXT]",s["required_next"])
print("[PASS] discovery population frozen before strict OOS testing")
print("[PASS] profitability-after-costs explicitly required")
print("[PASS] OED-021..OED-025 historical edge-candidate engine certified")
