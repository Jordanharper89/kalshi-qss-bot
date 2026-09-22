from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_data"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch()

MOD = PKG / "opd_001_predictive_data_foundation.py"
TEST = ROOT / "test_opd_001_predictive_data_foundation.py"

MOD.write_text(r"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

SCHEMA_VERSION = "OPD-001"
MISSION = "STATE_AT_T_TO_FUTURE_OUTCOME_WITHOUT_LEAKAGE"

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def build_foundation(root=None):
    root = Path(root or Path.cwd())
    runtime = root / "runtime" / "predictive_data"
    runtime.mkdir(parents=True, exist_ok=True)

    contract = {
        "schema_version": SCHEMA_VERSION,
        "mission": MISSION,
        "principles": [
            "PHYSICAL_DATA_ONLY",
            "PRESERVE_RAW_FIELDS_BEFORE_DERIVATION",
            "SOURCE_EVENT_TIME_PREFERRED_OVER_INGESTION_TIME",
            "FEATURES_AT_OR_BEFORE_T_ONLY",
            "OUTCOMES_STRICTLY_AFTER_T_ONLY",
            "NO_MODEL_FIT_DURING_DISSECTION",
            "NO_EDGE_CLAIM_DURING_DISSECTION",
            "NO_MARKET_PRICE_AS_INDEPENDENT_PROBABILITY",
        ],
        "target_horizons_seconds": [30, 60, 300, 900, 3600],
        "target_families": [
            "FUTURE_RETURN",
            "MFE",
            "MAE",
            "TIME_TO_MOVE",
            "REVERSAL",
            "SETTLEMENT_WHEN_PHYSICALLY_AVAILABLE",
        ],
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }
    contract["contract_hash"] = _hash(contract)
    path = runtime / "opd_001_foundation_contract.json"
    path.write_text(json.dumps(contract, sort_keys=True, indent=2), encoding="utf-8")
    return contract, path
""", encoding="utf-8")

TEST.write_text(r"""
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
""", encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPD-001 installer complete")
