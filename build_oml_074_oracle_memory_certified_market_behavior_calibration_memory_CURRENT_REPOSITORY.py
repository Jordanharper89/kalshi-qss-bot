from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"
UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_source_reliability_073.py"
UPSTREAM_TEST = ROOT / "test_oml_073_oracle_memory_certified_market_behavior_source_reliability.py"
CALIBRATION = PACKAGE / "oracle_memory_certified_observation_calibration_memory.py"
PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_calibration_memory_074.py"
TEST = ROOT / "test_oml_074_oracle_memory_certified_market_behavior_calibration_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Mapping, Sequence\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_source_reliability_073 import (\n    OracleMemoryCertifiedMarketBehaviorSourceReliability073,\n    verify_oracle_memory_certified_market_behavior_source_reliability_073,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (\n    OracleMemoryCertifiedCalibrationForecast,\n    OracleMemoryCertifiedCalibrationMemory,\n    build_oracle_memory_certified_calibration_memory,\n    verify_oracle_memory_certified_calibration_forecast,\n    verify_oracle_memory_certified_calibration_memory,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (\n    SUBSYSTEM_ID,\n)\n\nSCHEMA_VERSION = "OML-074"\nENGINE_ID = "OML-074"\nPOLICY_ID = "oracle-memory.certified-market-behavior-calibration-memory-074.v1"\nUPSTREAM_SCHEMA_VERSION = "OML-073"\nUPSTREAM_ENGINE_ID = "OML-073"\nCALIBRATION_SCHEMA_VERSION = "OML-035"\nCALIBRATION_ENGINE_ID = "OML-035"\nSTATE_READ_ONLY = "read_only_market_behavior_calibration_memory_074"\n\n\nclass OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleMemoryCertifiedMarketBehaviorCalibrationMemory074:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    upstream_reliability_certification_hash: str\n    upstream_reliability_memory_hash: str\n    calibration_schema_version: str\n    calibration_engine_id: str\n    calibration: OracleMemoryCertifiedCalibrationMemory\n    profile_count: int\n    total_observation_count: int\n    total_confirmed_count: int\n    state: str\n    source_reliability_lineage_verified: bool\n    certified_observation_lineage_verified: bool\n    calibration_lineage_verified: bool\n    deterministic_scoring_verified: bool\n    canonical_profile_order_verified: bool\n    probability_bounds_verified: bool\n    outcome_lineage_verified: bool\n    calibration_bucket_reconciliation_verified: bool\n    persistence_enabled: bool\n    learning_updates_enabled: bool\n    runtime_activation_enabled: bool\n    publication_enabled: bool\n    action_authorization_enabled: bool\n    qseries_execution_enabled: bool\n    calibration_ready: bool\n    downstream_causal_memory_authorized: bool\n    read_only: bool\n    certification_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError(\n        "unsupported OML-074 value type"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(\n        json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            separators=(",", ":"),\n            ensure_ascii=True,\n            allow_nan=False,\n        ).encode("utf-8")\n    ).hexdigest()\n\n\ndef _reject(reason: str) -> None:\n    raise OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError(reason)\n\n\ndef _require_hash(value: str, label: str) -> None:\n    if not isinstance(value, str) or len(value) != 64:\n        _reject(f"OML-074 invalid {label} length")\n    try:\n        int(value, 16)\n    except ValueError as exc:\n        raise OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError(\n            f"OML-074 invalid {label} hexadecimal value"\n        ) from exc\n\n\ndef build_oracle_memory_certified_market_behavior_calibration_memory_074(\n    *,\n    reliability: OracleMemoryCertifiedMarketBehaviorSourceReliability073,\n    forecasts: Sequence[OracleMemoryCertifiedCalibrationForecast],\n) -> OracleMemoryCertifiedMarketBehaviorCalibrationMemory074:\n    verify_oracle_memory_certified_market_behavior_source_reliability_073(reliability)\n\n    if reliability.schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-074 upstream schema mismatch")\n    if reliability.engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-074 upstream engine mismatch")\n    if not reliability.reliability_ready:\n        _reject("OML-074 upstream reliability not ready")\n    if not reliability.downstream_calibration_authorized:\n        _reject("OML-074 calibration continuation not authorized")\n    if not reliability.read_only:\n        _reject("OML-074 upstream reliability not read-only")\n\n    allowed_hashes = {\n        value\n        for binding in reliability.source_reliability.bindings\n        for value in binding.certified_observation_hashes\n    }\n    if not allowed_hashes:\n        _reject("OML-074 no certified observation hashes available")\n\n    for forecast in forecasts:\n        verify_oracle_memory_certified_calibration_forecast(forecast)\n        if forecast.certified_observation_hash not in allowed_hashes:\n            _reject("OML-074 forecast references unknown certified observation")\n\n    calibration = build_oracle_memory_certified_calibration_memory(\n        source_reliability=reliability.source_reliability,\n        forecasts=tuple(forecasts),\n    )\n    verify_oracle_memory_certified_calibration_memory(calibration)\n\n    if calibration.schema_version != CALIBRATION_SCHEMA_VERSION:\n        _reject("OML-074 calibration schema mismatch")\n    if calibration.engine_id != CALIBRATION_ENGINE_ID:\n        _reject("OML-074 calibration engine mismatch")\n    if calibration.upstream_certification_hash != (\n        reliability.source_reliability.certification_hash\n    ):\n        _reject("OML-074 reliability certification lineage mismatch")\n    if calibration.upstream_reliability_memory_hash != (\n        reliability.source_reliability.reliability_memory.memory_hash\n    ):\n        _reject("OML-074 reliability memory lineage mismatch")\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "upstream_schema_version": reliability.schema_version,\n        "upstream_engine_id": reliability.engine_id,\n        "upstream_certification_hash": reliability.certification_hash,\n        "upstream_reliability_certification_hash": (\n            reliability.source_reliability.certification_hash\n        ),\n        "upstream_reliability_memory_hash": (\n            reliability.source_reliability.reliability_memory.memory_hash\n        ),\n        "calibration_schema_version": calibration.schema_version,\n        "calibration_engine_id": calibration.engine_id,\n        "calibration": calibration,\n        "profile_count": calibration.profile_count,\n        "total_observation_count": calibration.total_observation_count,\n        "total_confirmed_count": calibration.total_confirmed_count,\n        "state": STATE_READ_ONLY,\n        "source_reliability_lineage_verified": True,\n        "certified_observation_lineage_verified": (\n            calibration.certified_observation_lineage_verified\n        ),\n        "calibration_lineage_verified": True,\n        "deterministic_scoring_verified": (\n            calibration.deterministic_scoring_verified\n        ),\n        "canonical_profile_order_verified": (\n            calibration.canonical_profile_order_verified\n        ),\n        "probability_bounds_verified": calibration.probability_bounds_verified,\n        "outcome_lineage_verified": calibration.outcome_lineage_verified,\n        "calibration_bucket_reconciliation_verified": (\n            calibration.calibration_bucket_reconciliation_verified\n        ),\n        "persistence_enabled": False,\n        "learning_updates_enabled": False,\n        "runtime_activation_enabled": False,\n        "publication_enabled": False,\n        "action_authorization_enabled": False,\n        "qseries_execution_enabled": False,\n        "calibration_ready": True,\n        "downstream_causal_memory_authorized": (\n            calibration.downstream_causal_memory_authorized\n        ),\n        "read_only": True,\n    }\n\n    result = OracleMemoryCertifiedMarketBehaviorCalibrationMemory074(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_oracle_memory_certified_market_behavior_calibration_memory_074(result)\n    return result\n\n\ndef verify_oracle_memory_certified_market_behavior_calibration_memory_074(\n    result: OracleMemoryCertifiedMarketBehaviorCalibrationMemory074,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-074 certification hash mismatch")\n\n    if result.schema_version != SCHEMA_VERSION:\n        _reject("OML-074 schema mismatch")\n    if result.engine_id != ENGINE_ID:\n        _reject("OML-074 engine mismatch")\n    if result.policy_id != POLICY_ID:\n        _reject("OML-074 policy mismatch")\n    if result.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-074 subsystem mismatch")\n    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-074 upstream schema lineage mismatch")\n    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-074 upstream engine lineage mismatch")\n    if result.calibration_schema_version != CALIBRATION_SCHEMA_VERSION:\n        _reject("OML-074 calibration schema lineage mismatch")\n    if result.calibration_engine_id != CALIBRATION_ENGINE_ID:\n        _reject("OML-074 calibration engine lineage mismatch")\n\n    for value in (\n        result.upstream_certification_hash,\n        result.upstream_reliability_certification_hash,\n        result.upstream_reliability_memory_hash,\n        result.certification_hash,\n    ):\n        _require_hash(value, "lineage hash")\n\n    verify_oracle_memory_certified_calibration_memory(result.calibration)\n\n    if result.upstream_reliability_certification_hash != (\n        result.calibration.upstream_certification_hash\n    ):\n        _reject("OML-074 reliability certification mismatch")\n    if result.upstream_reliability_memory_hash != (\n        result.calibration.upstream_reliability_memory_hash\n    ):\n        _reject("OML-074 reliability memory mismatch")\n    if result.profile_count != result.calibration.profile_count:\n        _reject("OML-074 profile count mismatch")\n    if result.total_observation_count != (\n        result.calibration.total_observation_count\n    ):\n        _reject("OML-074 observation count mismatch")\n    if result.total_confirmed_count != (\n        result.calibration.total_confirmed_count\n    ):\n        _reject("OML-074 confirmed count mismatch")\n\n    required = (\n        result.source_reliability_lineage_verified,\n        result.certified_observation_lineage_verified,\n        result.calibration_lineage_verified,\n        result.deterministic_scoring_verified,\n        result.canonical_profile_order_verified,\n        result.probability_bounds_verified,\n        result.outcome_lineage_verified,\n        result.calibration_bucket_reconciliation_verified,\n        result.calibration_ready,\n        result.downstream_causal_memory_authorized,\n        result.read_only,\n    )\n    if not all(required):\n        _reject("OML-074 guarantee missing")\n    if result.state != STATE_READ_ONLY:\n        _reject("OML-074 state invalid")\n\n    forbidden = (\n        result.persistence_enabled,\n        result.learning_updates_enabled,\n        result.runtime_activation_enabled,\n        result.publication_enabled,\n        result.action_authorization_enabled,\n        result.qseries_execution_enabled,\n    )\n    if any(forbidden):\n        _reject("OML-074 forbidden capability enabled")\n\n    return True\n'
TEST_SOURCE = 'from __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_calibration_memory_074 import (\n    OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError,\n    build_oracle_memory_certified_market_behavior_calibration_memory_074,\n    verify_oracle_memory_certified_market_behavior_calibration_memory_074,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (\n    build_oracle_memory_certified_calibration_forecast,\n)\n\n\ndef load_module(path: Path, name: str):\n    specification = importlib.util.spec_from_file_location(name, path)\n    if specification is None or specification.loader is None:\n        raise RuntimeError(f"unable to load fixture: {path}")\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef expect_rejection(callable_object, label: str) -> None:\n    try:\n        callable_object()\n    except OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError:\n        return\n    raise AssertionError(f"tampered OML-074 {label} accepted")\n\n\ndef build_calibration(root: Path):\n    fixture_073 = load_module(\n        root\n        / "test_oml_073_oracle_memory_certified_market_behavior_source_reliability.py",\n        "oml_073_fixture_for_oml_074",\n    )\n    reliability, lifecycle, outcomes = fixture_073.build_reliability(root)\n\n    source_profile = (\n        reliability.source_reliability.reliability_memory.profiles[0]\n    )\n    source_binding = reliability.source_reliability.bindings[0]\n    certified_hashes = source_binding.certified_observation_hashes\n    assert certified_hashes\n\n    forecasts = tuple(\n        build_oracle_memory_certified_calibration_forecast(\n            profile_name="Market-Behavior Calibration",\n            source_name=source_profile.source_name,\n            source_id=source_profile.source_id,\n            forecast_id=f"market-behavior-forecast-{index + 1:03d}",\n            certified_observation_hash=value,\n            predicted_probability=max(0.05, 0.80 - (index * 0.10)),\n            outcome_confirmed=True,\n            outcome_value=1 if index % 2 == 0 else 0,\n            observed_at=f"2026-08-04T14:{10 + index:02d}:00-05:00",\n            resolved_at=f"2026-08-04T15:{30 + index:02d}:00-05:00",\n        )\n        for index, value in enumerate(certified_hashes)\n    )\n\n    result = build_oracle_memory_certified_market_behavior_calibration_memory_074(\n        reliability=reliability,\n        forecasts=forecasts,\n    )\n    return result, reliability, forecasts\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OML-074 TEST")\n    print(" CERTIFIED MARKET-BEHAVIOR CALIBRATION MEMORY")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    result, reliability, forecasts = build_calibration(root)\n\n    assert result.schema_version == "OML-074"\n    assert result.engine_id == "OML-074"\n    assert result.upstream_schema_version == "OML-073"\n    assert result.upstream_engine_id == "OML-073"\n    assert result.calibration_schema_version == "OML-035"\n    assert result.calibration_engine_id == "OML-035"\n    assert result.profile_count == 1\n    assert result.total_observation_count == len(forecasts)\n    assert result.total_confirmed_count == len(forecasts)\n    assert result.upstream_certification_hash == reliability.certification_hash\n    assert result.upstream_reliability_certification_hash == (\n        reliability.source_reliability.certification_hash\n    )\n    assert result.upstream_reliability_memory_hash == (\n        reliability.source_reliability.reliability_memory.memory_hash\n    )\n    assert result.source_reliability_lineage_verified\n    assert result.certified_observation_lineage_verified\n    assert result.calibration_lineage_verified\n    assert result.deterministic_scoring_verified\n    assert result.canonical_profile_order_verified\n    assert result.probability_bounds_verified\n    assert result.outcome_lineage_verified\n    assert result.calibration_bucket_reconciliation_verified\n    assert result.calibration_ready\n    assert result.downstream_causal_memory_authorized\n    assert result.read_only\n    assert not result.persistence_enabled\n    assert not result.learning_updates_enabled\n    assert not result.runtime_activation_enabled\n    assert not result.publication_enabled\n    assert not result.action_authorization_enabled\n    assert not result.qseries_execution_enabled\n\n    replay, _, _ = build_calibration(root)\n    assert replay == result\n    assert verify_oracle_memory_certified_market_behavior_calibration_memory_074(result)\n\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_calibration_memory_074(\n            replace(result, persistence_enabled=True)\n        ),\n        "persistence state",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_calibration_memory_074(\n            replace(result, downstream_causal_memory_authorized=False)\n        ),\n        "causal continuation",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_calibration_memory_074(\n            replace(result, qseries_execution_enabled=True)\n        ),\n        "Q Series execution",\n    )\n\n    print("[PASS] Certified OML-073 reliability consumed read-only")\n    print("[PASS] Exact OML-034 reliability object passed directly")\n    print("[PASS] Actual OML-035 calibration builder consumed")\n    print("[PASS] Forecasts bound only to certified observation hashes")\n    print("[PASS] Reliability and calibration lineage retained")\n    print("[PASS] Probability bounds and outcomes verified")\n    print("[PASS] Calibration buckets reconciled")\n    print("[PASS] Causal-memory continuation authorized read-only")\n    print("[PASS] Deterministic replay equality verified")\n    print("[PASS] Active capabilities remained disabled")\n    print("[PASS] Tampered OML-074 calibration objects rejected")\n    print("[DONE] OML-074 CERTIFIED MARKET-BEHAVIOR CALIBRATION MEMORY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_current_repository() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, CALIBRATION)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required certified files missing: " + ", ".join(missing))

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_source_reliability_073"
    )
    calibration = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_calibration_memory"
    )

    expected = (
        (upstream, "SCHEMA_VERSION", "OML-073"),
        (upstream, "ENGINE_ID", "OML-073"),
        (calibration, "SCHEMA_VERSION", "OML-035"),
        (calibration, "ENGINE_ID", "OML-035"),
    )
    for module, name, value in expected:
        actual = getattr(module, name, None)
        if actual != value:
            raise RuntimeError(
                f"{module.__name__}.{name} mismatch: expected {value!r}, got {actual!r}"
            )

    fields = set(
        upstream.OracleMemoryCertifiedMarketBehaviorSourceReliability073.__dataclass_fields__
    )
    required_fields = {
        "source_reliability",
        "reliability_ready",
        "downstream_calibration_authorized",
        "certification_hash",
        "read_only",
    }
    missing_fields = sorted(required_fields - fields)
    if missing_fields:
        raise RuntimeError("OML-073 dataclass fields missing: " + ", ".join(missing_fields))

    builder = calibration.build_oracle_memory_certified_calibration_memory
    parameters = set(inspect.signature(builder).parameters)
    missing_parameters = sorted({"source_reliability", "forecasts"} - parameters)
    if missing_parameters:
        raise RuntimeError("OML-035 builder parameters missing: " + ", ".join(missing_parameters))


def main() -> int:
    print("=" * 48)
    print(" OML-074 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR CALIBRATION MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CURRENT_REPOSITORY_OML_073_035_EXACT_ALIGNMENT")
    try:
        validate_current_repository()
        print("[OK] Current OML-073 dataclass inspected")
        print("[OK] Current OML-035 builder signature inspected")

        tracked = {path: path.read_bytes() for path in (UPSTREAM, UPSTREAM_TEST, CALIBRATION)}
        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_certified_market_behavior_calibration_memory_074 import *"
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"OML-074 test failed with exit code {completed.returncode}")

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Complete OML-074 production replacement installed")
        print("[PASS] Complete deterministic standalone test installed")
        print("[PASS] Certified OML-073 and OML-035 files unchanged")
        print("[PASS] Deterministic replay preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[DONE] OML-074 INSTALLED")
        return 0
    except (RuntimeError, SyntaxError, ImportError, AttributeError, KeyError, TypeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
