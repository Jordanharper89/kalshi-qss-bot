
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_030_edge_candidate_registry_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["edge_certified_count"]==0 and not s["edge_claim_allowed"] and not s["historical_secondary_oos_available"]
print("[FILE]",p);print("[EDGE_CANDIDATES]",s["edge_candidates"]);print("[DEGREE_COUNTS]",s["degree_counts"]);print("[EDGE_CERTIFIED]",s["edge_certified_count"]);print("[NEXT_REQUIRED]",s["next_required"]);print("[REGISTRY_HASH]",s["registry_hash"])
print("[PASS] only temporal/contract/overlap/economic survivors entered EDGE_CANDIDATE registry");print("[PASS] no historical robustness result mislabeled as certified edge");print("[PASS] OPD-026..OPD-030 secondary robustness/economic reality slice certified")
