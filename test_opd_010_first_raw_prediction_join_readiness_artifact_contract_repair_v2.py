
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_010_first_raw_prediction_join_readiness_artifact_contract_repair_v2 import build

s, p = build(Path.cwd())

assert p.exists()
assert s["raw_join_pavement_ready"] is True
assert all(s["checks"].values())
assert s["model_fit_allowed"] is False
assert s["formula_mining_allowed"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False

print("[FILE]", p)
print("[RESOLVED_INTERFACES]", s["resolved_interfaces"])
print("[CHECKS]", s["checks"])
print("[RAW_JOIN_PAVEMENT_READY]", s["raw_join_pavement_ready"])
print("[MODEL_FIT_ALLOWED]", s["model_fit_allowed"])
print("[FORMULA_MINING_ALLOWED]", s["formula_mining_allowed"])
print("[NEXT_REQUIRED]", s["next_required"])
print("[HASH]", s["hash"])
print("[PASS] Python-filename dependency assertions retired")
print("[PASS] OPD-010 bound only to certified runtime artifact contracts")
print("[PASS] raw prediction join pavement ready")
print("[PASS] OPD-010 ARTIFACT CONTRACT REPAIR V2 certified")
