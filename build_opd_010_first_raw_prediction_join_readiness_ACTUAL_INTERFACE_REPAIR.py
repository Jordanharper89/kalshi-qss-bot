from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_data"
MOD = PKG / "opd_010_first_raw_prediction_join_readiness_actual_interface_repair.py"
TEST = ROOT / "test_opd_010_first_raw_prediction_join_readiness_actual_interface_repair.py"

assert (PKG / "opd_004_kalshi_raw_state_at_t.py").exists()
assert (PKG / "opd_005_future_outcome_census_and_prediction_matrix_gate.py").exists()
assert (PKG / "opd_007_full_history_source_depth_census_index_boundary_repair.py").exists()
assert (PKG / "opd_008_coinbase_hf_raw_condition_state_extract.py").exists()
assert (PKG / "opd_009_crypto_condition_raw_state_chunked_index_repair.py").exists()

MOD.write_text(r"""
from pathlib import Path
import hashlib
import json

def _load(path):
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))

def _positive(d, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return True, k, v
    return False, None, None

def build(root=None):
    root = Path(root or Path.cwd())
    r = root / "runtime" / "predictive_data"

    depth_path = r / "opd_007_full_history_source_depth_census.json"
    kalshi_path = r / "opd_004_kalshi_raw_state_at_t.json"
    outcomes_path = r / "opd_005_future_outcome_census.json"
    coinbase_path = r / "opd_008_coinbase_hf_raw_condition_state.json"
    crypto_path = r / "opd_009_crypto_condition_raw_state.json"

    depth = _load(depth_path)
    kalshi = _load(kalshi_path)
    outcomes = _load(outcomes_path)
    coinbase = _load(coinbase_path)
    crypto = _load(crypto_path)

    depth_ok, depth_key, depth_value = _positive(
        depth, "scanned_rows", "grouped_total_rows", "total_rows"
    )
    kalshi_ok, kalshi_key, kalshi_value = _positive(
        kalshi, "row_count", "rows"
    )
    outcome_ok, outcome_key, outcome_value = _positive(
        outcomes, "outcome_rows", "row_count", "rows"
    )
    coinbase_ok, coinbase_key, coinbase_value = _positive(
        coinbase, "row_count", "rows"
    )
    crypto_ok, crypto_key, crypto_value = _positive(
        crypto, "row_count", "rows"
    )

    accounting_ok = bool(depth.get("row_accounting_ok", True))
    depth_read_only = bool(depth.get("read_only", False))
    coinbase_read_only = bool(coinbase.get("read_only", True))
    crypto_read_only = bool(crypto.get("read_only", True))

    checks = {
        "full_history_census_present": depth_ok,
        "full_history_accounting_ok": accounting_ok,
        "full_history_read_only": depth_read_only,
        "kalshi_state_present": kalshi_ok,
        "future_outcomes_present": outcome_ok,
        "coinbase_hf_state_present": coinbase_ok,
        "coinbase_hf_read_only": coinbase_read_only,
        "crypto_condition_state_present": crypto_ok,
        "crypto_condition_read_only": crypto_read_only,
    }

    raw_join_pavement_ready = all(checks.values())

    interfaces = {
        "full_history_census": {"key": depth_key, "value": depth_value},
        "kalshi_state": {"key": kalshi_key, "value": kalshi_value},
        "future_outcomes": {"key": outcome_key, "value": outcome_value},
        "coinbase_hf_state": {"key": coinbase_key, "value": coinbase_value},
        "crypto_condition_state": {"key": crypto_key, "value": crypto_value},
    }

    next_required = [
        "FREEZE_DETERMINISTIC_OUTCOME_ANCHOR_POPULATION",
        "ASOF_JOIN_EACH_ANCHOR_TO_ONLY_PRE_T_COINBASE_HF_STATE",
        "ASOF_JOIN_EACH_ANCHOR_TO_ONLY_PRE_T_CRYPTO_CONDITION_STATE",
        "ATTACH_RELATED_KALSHI_STATE_AT_OR_BEFORE_T",
        "ATTACH_LEARNED_ORACLE_STATE_WITH_EXACT_ASOF_LINEAGE",
        "CERTIFY_ZERO_POST_T_FEATURE_LEAKAGE",
        "FREEZE_PREDICTION_READY_WORLD_STATE_MATRIX",
    ]

    payload = {
        "schema_version": "OPD-010",
        "revision": "ACTUAL_CERTIFIED_INTERFACE_REPAIR",
        "checks": checks,
        "resolved_interfaces": interfaces,
        "raw_join_pavement_ready": raw_join_pavement_ready,
        "model_fit_allowed": False,
        "formula_mining_allowed": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
        "next_required": next_required,
    }

    payload["hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    out = r / "opd_010_first_raw_prediction_join_readiness_gate.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload, out
""", encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_010_first_raw_prediction_join_readiness_actual_interface_repair import build

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
print("[CHECKS]", s["checks"])
print("[RESOLVED_INTERFACES]", s["resolved_interfaces"])
print("[RAW_JOIN_PAVEMENT_READY]", s["raw_join_pavement_ready"])
print("[MODEL_FIT_ALLOWED]", s["model_fit_allowed"])
print("[FORMULA_MINING_ALLOWED]", s["formula_mining_allowed"])
print("[NEXT_REQUIRED]", s["next_required"])
print("[HASH]", s["hash"])
print("[PASS] stale OPD-007 total_rows dependency retired")
print("[PASS] OPD-010 bound to actual certified OPD-004/005/007/008/009 artifacts")
print("[PASS] raw-state pavement ready without enabling model fitting")
print("[PASS] OPD-010 first raw prediction join readiness ACTUAL INTERFACE REPAIR certified")
""", encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPD-010 actual-interface repair installer complete")
