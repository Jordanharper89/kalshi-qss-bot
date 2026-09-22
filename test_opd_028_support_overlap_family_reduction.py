
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_028_support_overlap_family_reduction import build
s,p=build(Path.cwd());assert p.exists() and s["representatives"]<=s["input_cross_contract_pass"] and s["edge_certified_count"]==0
print("[FILE]",p);print("[INPUT]",s["input_cross_contract_pass"]);print("[REPRESENTATIVES]",s["representatives"]);print("[COLLAPSED_BY_OVERLAP]",s["collapsed_by_overlap"]);print("[JACCARD]",s["jaccard_threshold"]);print("[REGISTRY_HASH]",s["registry_hash"]);print("[PASS] OPD-028 support-overlap family reduction certified")
