
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
