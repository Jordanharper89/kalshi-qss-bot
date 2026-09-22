
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_029_transaction_hurdle_and_path_quality_gate import build
s,p=build(Path.cwd());assert p.exists() and not s["assumptions_tuned_on_validation"] and s["edge_certified_count"]==0
print("[FILE]",p);print("[EVALUATED]",s["evaluated"]);print("[ECONOMIC_PASS]",s["economic_gate_pass"]);print("[FIXED_ASSUMPTIONS]",s["fixed_assumptions"]);print("[REGISTRY_HASH]",s["registry_hash"]);print("[PASS] OPD-029 transaction-hurdle/path-quality gate certified")
