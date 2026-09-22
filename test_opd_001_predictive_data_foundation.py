
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_001_predictive_data_foundation import build_foundation

s, p = build_foundation(Path.cwd())
assert p.exists()
assert s["mission"] == "STATE_AT_T_TO_FUTURE_OUTCOME_WITHOUT_LEAKAGE"
assert "PRESERVE_RAW_FIELDS_BEFORE_DERIVATION" in s["principles"]
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
print("[FOUNDATION]", p)
print("[CONTRACT_HASH]", s["contract_hash"])
print("[PASS] raw-before-derived predictive-data contract established")
print("[PASS] state-at-T and future-outcome separation established")
print("[PASS] OPD-001 predictive-data foundation certified")
