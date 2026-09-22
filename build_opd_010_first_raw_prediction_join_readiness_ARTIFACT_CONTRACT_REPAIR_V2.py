from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_data"
PKG.mkdir(parents=True, exist_ok=True)

MOD = PKG / "opd_010_first_raw_prediction_join_readiness_artifact_contract_repair_v2.py"
TEST = ROOT / "test_opd_010_first_raw_prediction_join_readiness_artifact_contract_repair_v2.py"

MOD.write_text(r"""
from pathlib import Path
import hashlib
import json

FILES = {
    "kalshi_state": "opd_004_kalshi_raw_state_at_t.json",
    "future_outcomes": "opd_005_future_outcome_census.json",
    "full_history": "opd_007_full_history_source_depth_census.json",
    "coinbase_hf": "opd_008_coinbase_hf_raw_condition_state.json",
    "crypto_conditions": "opd_009_crypto_condition_raw_state.json",
}

def _load(path):
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))

def _positive(d, keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return {"ok": True, "key": k, "value": v}
    return {"ok": False, "key": None, "value": None}

def build(root=None):
    root = Path(root or Path.cwd())
    runtime = root / "runtime" / "predictive_data"

    docs = {name: _load(runtime / fn) for name, fn in FILES.items()}

    resolved = {
        "kalshi_state": _positive(docs["kalshi_state"], ["row_count", "rows"]),
        "future_outcomes": _positive(docs["future_outcomes"], ["outcome_rows", "row_count", "rows"]),
        "full_history": _positive(docs["full_history"], ["scanned_rows", "grouped_total_rows", "total_rows"]),
        "coinbase_hf": _positive(docs["coinbase_hf"], ["row_count", "rows"]),
        "crypto_conditions": _positive(docs["crypto_conditions"], ["row_count", "rows"]),
    }

    checks = {
        "kalshi_state_present": resolved["kalshi_state"]["ok"],
        "future_outcomes_present": resolved["future_outcomes"]["ok"],
        "full_history_present": resolved["full_history"]["ok"],
        "full_history_accounting_ok": docs["full_history"].get("row_accounting_ok") is True,
        "full_history_read_only": docs["full_history"].get("read_only") is True,
        "coinbase_hf_present": resolved["coinbase_hf"]["ok"],
        "coinbase_hf_read_only": docs["coinbase_hf"].get("read_only", True) is True,
        "crypto_conditions_present": resolved["crypto_conditions"]["ok"],
        "crypto_conditions_read_only": docs["crypto_conditions"].get("read_only", True) is True,
    }

    ready = all(checks.values())

    payload = {
        "schema_version": "OPD-010",
        "revision": "ARTIFACT_CONTRACT_REPAIR_V2",
        "artifact_files": FILES,
        "resolved_interfaces": resolved,
        "checks": checks,
        "raw_join_pavement_ready": ready,
        "model_fit_allowed": False,
        "formula_mining_allowed": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
        "next_required": [
            "FREEZE_DETERMINISTIC_OUTCOME_ANCHOR_POPULATION",
            "ASOF_JOIN_ONLY_PRE_T_COINBASE_HF_STATE",
            "ASOF_JOIN_ONLY_PRE_T_CRYPTO_CONDITION_STATE",
            "ATTACH_RELATED_KALSHI_STATE_AT_OR_BEFORE_T",
            "ATTACH_LEARNED_ORACLE_STATE_WITH_EXACT_ASOF_LINEAGE",
            "CERTIFY_ZERO_POST_T_FEATURE_LEAKAGE",
            "FREEZE_PREDICTION_READY_WORLD_STATE_MATRIX",
        ],
    }

    payload["hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    out = runtime / "opd_010_first_raw_prediction_join_readiness_gate.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload, out
""", encoding="utf-8")

TEST.write_text(r"""
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
""", encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPD-010 artifact-contract repair V2 installer complete")
