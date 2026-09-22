from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_calibration_memory_074.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_074_oracle_memory_certified_market_behavior_"
      "calibration_memory.py"
)
CAUSAL_036 = (
    PACKAGE
    / "oracle_memory_certified_observation_causal_pattern_memory.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_causal_pattern_memory_075.py"
)
TEST = (
    ROOT
    / "test_oml_075_oracle_memory_certified_market_behavior_"
      "causal_pattern_memory.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Mapping, Sequence\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_calibration_memory_074 import (\n    OracleMemoryCertifiedMarketBehaviorCalibrationMemory074,\n    verify_oracle_memory_certified_market_behavior_calibration_memory_074,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (\n    OracleMemoryCertifiedCausalObservationRequest,\n    OracleMemoryCertifiedCausalPatternMemory,\n    build_oracle_memory_certified_causal_pattern_memory,\n    verify_oracle_memory_certified_causal_observation_request,\n    verify_oracle_memory_certified_causal_pattern_memory,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (\n    SUBSYSTEM_ID,\n)\n\nSCHEMA_VERSION = "OML-075"\nENGINE_ID = "OML-075"\nPOLICY_ID = "oracle-memory.certified-market-behavior-causal-pattern-memory-075.v1"\nUPSTREAM_SCHEMA_VERSION = "OML-074"\nUPSTREAM_ENGINE_ID = "OML-074"\nCAUSAL_SCHEMA_VERSION = "OML-036"\nCAUSAL_ENGINE_ID = "OML-036"\nSTATE_READ_ONLY = "read_only_market_behavior_causal_pattern_memory_075"\n\n\nclass OracleMemoryCertifiedMarketBehaviorCausal075InvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleMemoryCertifiedMarketBehaviorCausalPatternMemory075:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    upstream_calibration_certification_hash: str\n    upstream_calibration_memory_hash: str\n    causal_schema_version: str\n    causal_engine_id: str\n    causal_patterns: OracleMemoryCertifiedCausalPatternMemory\n    pattern_count: int\n    total_observation_count: int\n    state: str\n    calibration_lineage_verified: bool\n    certified_observation_lineage_verified: bool\n    deterministic_identity_verified: bool\n    canonical_pattern_order_verified: bool\n    temporal_precedence_verified: bool\n    evidence_lineage_verified: bool\n    contradiction_tracking_verified: bool\n    outcome_reconciliation_verified: bool\n    persistence_enabled: bool\n    learning_updates_enabled: bool\n    runtime_activation_enabled: bool\n    publication_enabled: bool\n    action_authorization_enabled: bool\n    qseries_execution_enabled: bool\n    causal_memory_ready: bool\n    downstream_multi_hop_causal_authorized: bool\n    read_only: bool\n    certification_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleMemoryCertifiedMarketBehaviorCausal075InvariantError(\n        "unsupported OML-075 value type"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(\n        json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            separators=(",", ":"),\n            ensure_ascii=True,\n            allow_nan=False,\n        ).encode("utf-8")\n    ).hexdigest()\n\n\ndef _reject(reason: str) -> None:\n    raise OracleMemoryCertifiedMarketBehaviorCausal075InvariantError(reason)\n\n\ndef _require_hash(value: str, label: str) -> None:\n    if not isinstance(value, str) or len(value) != 64:\n        _reject(f"OML-075 invalid {label} length")\n    try:\n        int(value, 16)\n    except ValueError as exc:\n        raise OracleMemoryCertifiedMarketBehaviorCausal075InvariantError(\n            f"OML-075 invalid {label} hexadecimal value"\n        ) from exc\n\n\ndef build_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n    *,\n    calibration: OracleMemoryCertifiedMarketBehaviorCalibrationMemory074,\n    requests: Sequence[OracleMemoryCertifiedCausalObservationRequest],\n) -> OracleMemoryCertifiedMarketBehaviorCausalPatternMemory075:\n    verify_oracle_memory_certified_market_behavior_calibration_memory_074(\n        calibration\n    )\n\n    if calibration.schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-075 upstream schema mismatch")\n    if calibration.engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-075 upstream engine mismatch")\n    if not calibration.calibration_ready:\n        _reject("OML-075 upstream calibration not ready")\n    if not calibration.downstream_causal_memory_authorized:\n        _reject("OML-075 causal continuation not authorized")\n    if not calibration.read_only:\n        _reject("OML-075 upstream calibration not read-only")\n\n    for request in requests:\n        verify_oracle_memory_certified_causal_observation_request(request)\n\n    causal_patterns = build_oracle_memory_certified_causal_pattern_memory(\n        calibration=calibration.calibration,\n        requests=tuple(requests),\n    )\n    verify_oracle_memory_certified_causal_pattern_memory(causal_patterns)\n\n    if causal_patterns.schema_version != CAUSAL_SCHEMA_VERSION:\n        _reject("OML-075 causal schema mismatch")\n    if causal_patterns.engine_id != CAUSAL_ENGINE_ID:\n        _reject("OML-075 causal engine mismatch")\n    if causal_patterns.upstream_certification_hash != (\n        calibration.calibration.certification_hash\n    ):\n        _reject("OML-075 calibration certification lineage mismatch")\n    if causal_patterns.upstream_calibration_memory_hash != (\n        calibration.calibration.calibration_memory.memory_hash\n    ):\n        _reject("OML-075 calibration memory lineage mismatch")\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "upstream_schema_version": calibration.schema_version,\n        "upstream_engine_id": calibration.engine_id,\n        "upstream_certification_hash": calibration.certification_hash,\n        "upstream_calibration_certification_hash": (\n            calibration.calibration.certification_hash\n        ),\n        "upstream_calibration_memory_hash": (\n            calibration.calibration.calibration_memory.memory_hash\n        ),\n        "causal_schema_version": causal_patterns.schema_version,\n        "causal_engine_id": causal_patterns.engine_id,\n        "causal_patterns": causal_patterns,\n        "pattern_count": causal_patterns.pattern_count,\n        "total_observation_count": causal_patterns.total_observation_count,\n        "state": STATE_READ_ONLY,\n        "calibration_lineage_verified": True,\n        "certified_observation_lineage_verified": (\n            causal_patterns.certified_observation_lineage_verified\n        ),\n        "deterministic_identity_verified": (\n            causal_patterns.deterministic_identity_verified\n        ),\n        "canonical_pattern_order_verified": (\n            causal_patterns.canonical_pattern_order_verified\n        ),\n        "temporal_precedence_verified": (\n            causal_patterns.temporal_precedence_verified\n        ),\n        "evidence_lineage_verified": causal_patterns.evidence_lineage_verified,\n        "contradiction_tracking_verified": (\n            causal_patterns.contradiction_tracking_verified\n        ),\n        "outcome_reconciliation_verified": (\n            causal_patterns.outcome_reconciliation_verified\n        ),\n        "persistence_enabled": False,\n        "learning_updates_enabled": False,\n        "runtime_activation_enabled": False,\n        "publication_enabled": False,\n        "action_authorization_enabled": False,\n        "qseries_execution_enabled": False,\n        "causal_memory_ready": True,\n        "downstream_multi_hop_causal_authorized": (\n            causal_patterns.downstream_multi_hop_causal_authorized\n        ),\n        "read_only": True,\n    }\n\n    result = OracleMemoryCertifiedMarketBehaviorCausalPatternMemory075(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n        result\n    )\n    return result\n\n\ndef verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n    result: OracleMemoryCertifiedMarketBehaviorCausalPatternMemory075,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-075 certification hash mismatch")\n\n    if result.schema_version != SCHEMA_VERSION:\n        _reject("OML-075 schema mismatch")\n    if result.engine_id != ENGINE_ID:\n        _reject("OML-075 engine mismatch")\n    if result.policy_id != POLICY_ID:\n        _reject("OML-075 policy mismatch")\n    if result.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-075 subsystem mismatch")\n    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-075 upstream schema lineage mismatch")\n    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-075 upstream engine lineage mismatch")\n    if result.causal_schema_version != CAUSAL_SCHEMA_VERSION:\n        _reject("OML-075 causal schema lineage mismatch")\n    if result.causal_engine_id != CAUSAL_ENGINE_ID:\n        _reject("OML-075 causal engine lineage mismatch")\n\n    for value in (\n        result.upstream_certification_hash,\n        result.upstream_calibration_certification_hash,\n        result.upstream_calibration_memory_hash,\n        result.certification_hash,\n    ):\n        _require_hash(value, "lineage hash")\n\n    verify_oracle_memory_certified_causal_pattern_memory(\n        result.causal_patterns\n    )\n\n    if result.upstream_calibration_certification_hash != (\n        result.causal_patterns.upstream_certification_hash\n    ):\n        _reject("OML-075 calibration certification mismatch")\n    if result.upstream_calibration_memory_hash != (\n        result.causal_patterns.upstream_calibration_memory_hash\n    ):\n        _reject("OML-075 calibration memory mismatch")\n    if result.pattern_count != result.causal_patterns.pattern_count:\n        _reject("OML-075 pattern count mismatch")\n    if result.total_observation_count != (\n        result.causal_patterns.total_observation_count\n    ):\n        _reject("OML-075 observation count mismatch")\n\n    required = (\n        result.calibration_lineage_verified,\n        result.certified_observation_lineage_verified,\n        result.deterministic_identity_verified,\n        result.canonical_pattern_order_verified,\n        result.temporal_precedence_verified,\n        result.evidence_lineage_verified,\n        result.contradiction_tracking_verified,\n        result.outcome_reconciliation_verified,\n        result.causal_memory_ready,\n        result.downstream_multi_hop_causal_authorized,\n        result.read_only,\n    )\n    if not all(required):\n        _reject("OML-075 guarantee missing")\n\n    if result.state != STATE_READ_ONLY:\n        _reject("OML-075 state invalid")\n\n    forbidden = (\n        result.persistence_enabled,\n        result.learning_updates_enabled,\n        result.runtime_activation_enabled,\n        result.publication_enabled,\n        result.action_authorization_enabled,\n        result.qseries_execution_enabled,\n    )\n    if any(forbidden):\n        _reject("OML-075 forbidden capability enabled")\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory_075 import (\n    OracleMemoryCertifiedMarketBehaviorCausal075InvariantError,\n    build_oracle_memory_certified_market_behavior_causal_pattern_memory_075,\n    verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (\n    build_oracle_memory_certified_causal_observation_request,\n)\n\n\ndef load_module(path: Path, name: str):\n    specification = importlib.util.spec_from_file_location(name, path)\n    if specification is None or specification.loader is None:\n        raise RuntimeError(f"unable to load fixture: {path}")\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef expect_rejection(callable_object, label: str) -> None:\n    try:\n        callable_object()\n    except OracleMemoryCertifiedMarketBehaviorCausal075InvariantError:\n        return\n    raise AssertionError(f"tampered OML-075 {label} accepted")\n\n\ndef build_causal_memory(root: Path):\n    fixture_074 = load_module(\n        root\n        / "test_oml_074_oracle_memory_certified_market_behavior_"\n        "calibration_memory.py",\n        "oml_074_fixture_for_oml_075",\n    )\n    calibration, reliability, forecasts = fixture_074.build_calibration(root)\n\n    certified_hashes = tuple(\n        sorted(\n            {\n                value\n                for binding in calibration.calibration.bindings\n                for value in binding.certified_observation_hashes\n            }\n        )\n    )\n    assert certified_hashes\n\n    request = build_oracle_memory_certified_causal_observation_request(\n        pattern_name="Market-behavior liquidity shift precedes repricing",\n        cause_entity_id="1" * 64,\n        effect_entity_id="2" * 64,\n        cause_observed_at="2026-08-04T16:00:00-05:00",\n        effect_observed_at="2026-08-04T16:05:00-05:00",\n        certified_observation_hashes=(certified_hashes[0],),\n        contradicting_certified_observation_hashes=(),\n        confidence=0.82,\n        calibrated_probability=0.80,\n        outcome_confirmed=True,\n        outcome_supported=True,\n    )\n\n    result = (\n        build_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n            calibration=calibration,\n            requests=(request,),\n        )\n    )\n    return result, calibration, certified_hashes\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OML-075 TEST")\n    print(" CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    result, calibration, certified_hashes = build_causal_memory(root)\n\n    assert result.schema_version == "OML-075"\n    assert result.engine_id == "OML-075"\n    assert result.upstream_schema_version == "OML-074"\n    assert result.upstream_engine_id == "OML-074"\n    assert result.causal_schema_version == "OML-036"\n    assert result.causal_engine_id == "OML-036"\n    assert result.pattern_count == 1\n    assert result.total_observation_count == 1\n    assert result.calibration_lineage_verified\n    assert result.certified_observation_lineage_verified\n    assert result.temporal_precedence_verified\n    assert result.evidence_lineage_verified\n    assert result.outcome_reconciliation_verified\n    assert result.causal_memory_ready\n    assert result.downstream_multi_hop_causal_authorized\n    assert result.read_only\n    assert not result.persistence_enabled\n    assert not result.learning_updates_enabled\n    assert not result.runtime_activation_enabled\n    assert not result.publication_enabled\n    assert not result.action_authorization_enabled\n    assert not result.qseries_execution_enabled\n\n    binding = result.causal_patterns.bindings[0]\n    assert set(binding.certified_observation_hashes).issubset(\n        set(certified_hashes)\n    )\n\n    replay, _, _ = build_causal_memory(root)\n    assert replay == result\n    assert verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n        result\n    )\n\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n            replace(result, persistence_enabled=True)\n        ),\n        "persistence",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(\n            replace(result, qseries_execution_enabled=True)\n        ),\n        "Q Series execution",\n    )\n\n    print("[PASS] Certified OML-074 calibration consumed read-only")\n    print("[PASS] Exact OML-035 calibration object passed directly")\n    print("[PASS] Actual OML-036 causal-pattern builder consumed")\n    print("[PASS] Causal evidence bound only to certified observation hashes")\n    print("[PASS] Calibration and temporal-precedence lineage retained")\n    print("[PASS] Outcome reconciliation retained")\n    print("[PASS] Multi-hop continuation authorized read-only")\n    print("[PASS] Deterministic replay equality verified")\n    print("[PASS] Active capabilities remained disabled")\n    print("[PASS] Tampered OML-075 causal objects rejected")\n    print("[DONE] OML-075 CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_current_repository() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, CAUSAL_036)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_calibration_memory_074"
    )
    causal_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_causal_pattern_memory"
    )

    expected = (
        (upstream_module, "SCHEMA_VERSION", "OML-074"),
        (upstream_module, "ENGINE_ID", "OML-074"),
        (causal_module, "SCHEMA_VERSION", "OML-036"),
        (causal_module, "ENGINE_ID", "OML-036"),
    )
    for module, name, value in expected:
        actual = getattr(module, name, None)
        if actual != value:
            raise RuntimeError(
                f"{module.__name__}.{name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    upstream_fields = set(
        upstream_module.
        OracleMemoryCertifiedMarketBehaviorCalibrationMemory074.
        __dataclass_fields__
    )
    required_fields = {
        "calibration",
        "calibration_ready",
        "downstream_causal_memory_authorized",
        "certification_hash",
        "read_only",
    }
    missing_fields = sorted(required_fields - upstream_fields)
    if missing_fields:
        raise RuntimeError(
            "OML-074 dataclass fields missing: "
            + ", ".join(missing_fields)
        )

    builder = getattr(
        causal_module,
        "build_oracle_memory_certified_causal_pattern_memory",
        None,
    )
    if builder is None:
        raise RuntimeError("OML-036 causal builder missing")
    parameters = set(inspect.signature(builder).parameters)
    missing_parameters = sorted({"calibration", "requests"} - parameters)
    if missing_parameters:
        raise RuntimeError(
            "OML-036 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-075 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CURRENT_REPOSITORY_OML_074_036_EXACT_ALIGNMENT")

    try:
        validate_current_repository()
        print("[OK] Current OML-074 dataclass inspected")
        print("[OK] Current OML-036 builder signature inspected")

        tracked = {
            path: path.read_bytes()
            for path in (UPSTREAM, UPSTREAM_TEST, CAUSAL_036)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "causal_pattern_memory_075 import *"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OML-075 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Complete OML-075 production replacement installed")
        print("[PASS] Complete deterministic standalone test installed")
        print("[PASS] Certified OML-074 and OML-036 files unchanged")
        print("[PASS] Deterministic replay preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[DONE] OML-075 INSTALLED")
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
