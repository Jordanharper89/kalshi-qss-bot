
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_027_cross_contract_concentration_gate import build
s,p=build(Path.cwd());assert p.exists() and not s["thresholds_tuned_on_validation"] and s["edge_certified_count"]==0
print("[FILE]",p);print("[EVALUATED]",s["evaluated"]);print("[CROSS_CONTRACT_PASS]",s["cross_contract_pass"]);print("[FIXED_THRESHOLDS]",s["fixed_thresholds"]);print("[REGISTRY_HASH]",s["registry_hash"]);print("[PASS] OPD-027 cross-contract concentration gate certified")
