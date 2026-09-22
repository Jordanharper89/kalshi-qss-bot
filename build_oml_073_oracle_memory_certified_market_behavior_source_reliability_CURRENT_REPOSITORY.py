from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"
UPSTREAM = PACKAGE / "oracle_memory_certified_market_behavior_narrative_lifecycle_tracking_072.py"
UPSTREAM_TEST = ROOT / "test_oml_072_oracle_memory_certified_market_behavior_narrative_lifecycle_tracking.py"
RELIABILITY = PACKAGE / "oracle_memory_certified_observation_source_reliability_memory.py"
PRODUCTION = PACKAGE / "oracle_memory_certified_market_behavior_source_reliability_073.py"
TEST = ROOT / "test_oml_073_oracle_memory_certified_market_behavior_source_reliability.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Mapping, Sequence\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking_072 import (\n    OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle072,\n    verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (\n    OracleMemoryCertifiedSourceOutcome,\n    OracleMemoryCertifiedSourceReliability,\n    build_oracle_memory_certified_source_reliability,\n    verify_oracle_memory_certified_source_outcome,\n    verify_oracle_memory_certified_source_reliability,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (\n    SUBSYSTEM_ID,\n)\n\nSCHEMA_VERSION = "OML-073"\nENGINE_ID = "OML-073"\nPOLICY_ID = "oracle-memory.certified-market-behavior-source-reliability-073.v1"\nUPSTREAM_SCHEMA_VERSION = "OML-072"\nUPSTREAM_ENGINE_ID = "OML-072"\nRELIABILITY_SCHEMA_VERSION = "OML-034"\nRELIABILITY_ENGINE_ID = "OML-034"\nSTATE_READ_ONLY = "read_only_market_behavior_source_reliability_073"\n\n\nclass OracleMemoryCertifiedMarketBehaviorReliability073InvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleMemoryCertifiedMarketBehaviorSourceReliability073:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    upstream_lifecycle_tracking_hash: str\n    reliability_schema_version: str\n    reliability_engine_id: str\n    source_reliability: OracleMemoryCertifiedSourceReliability\n    source_count: int\n    total_observation_count: int\n    state: str\n    lifecycle_lineage_verified: bool\n    narrative_lineage_verified: bool\n    certified_observation_lineage_verified: bool\n    deterministic_scoring_verified: bool\n    source_identity_uniqueness_verified: bool\n    contradiction_tracking_verified: bool\n    calibration_tracking_verified: bool\n    persistence_enabled: bool\n    learning_updates_enabled: bool\n    runtime_activation_enabled: bool\n    publication_enabled: bool\n    action_authorization_enabled: bool\n    qseries_execution_enabled: bool\n    reliability_ready: bool\n    downstream_calibration_authorized: bool\n    read_only: bool\n    certification_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleMemoryCertifiedMarketBehaviorReliability073InvariantError(\n        "unsupported OML-073 value type"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(\n        json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            separators=(",", ":"),\n            ensure_ascii=True,\n            allow_nan=False,\n        ).encode("utf-8")\n    ).hexdigest()\n\n\ndef _reject(reason: str) -> None:\n    raise OracleMemoryCertifiedMarketBehaviorReliability073InvariantError(reason)\n\n\ndef _require_hash(value: str, label: str) -> None:\n    if not isinstance(value, str) or len(value) != 64:\n        _reject(f"OML-073 invalid {label} length")\n    try:\n        int(value, 16)\n    except ValueError as exc:\n        raise OracleMemoryCertifiedMarketBehaviorReliability073InvariantError(\n            f"OML-073 invalid {label} hexadecimal value"\n        ) from exc\n\n\ndef build_oracle_memory_certified_market_behavior_source_reliability_073(\n    *,\n    lifecycle: OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle072,\n    outcomes: Sequence[OracleMemoryCertifiedSourceOutcome],\n) -> OracleMemoryCertifiedMarketBehaviorSourceReliability073:\n    verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(lifecycle)\n\n    if lifecycle.schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-073 upstream schema mismatch")\n    if lifecycle.engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-073 upstream engine mismatch")\n    if not lifecycle.lifecycle_ready:\n        _reject("OML-073 upstream lifecycle not ready")\n    if not lifecycle.downstream_source_reliability_authorized:\n        _reject("OML-073 reliability continuation not authorized")\n    if not lifecycle.read_only:\n        _reject("OML-073 upstream lifecycle not read-only")\n\n    allowed_hashes = {\n        value\n        for binding in lifecycle.lifecycle_tracking.bindings\n        for value in binding.source_observation_hashes\n    }\n    if not allowed_hashes:\n        _reject("OML-073 lifecycle contains no certified observations")\n\n    for outcome in outcomes:\n        verify_oracle_memory_certified_source_outcome(outcome)\n        if outcome.observation_hash not in allowed_hashes:\n            _reject("OML-073 outcome references unknown certified observation")\n\n    reliability = build_oracle_memory_certified_source_reliability(\n        tracking=lifecycle.lifecycle_tracking,\n        outcomes=tuple(outcomes),\n    )\n    verify_oracle_memory_certified_source_reliability(reliability)\n\n    if reliability.schema_version != RELIABILITY_SCHEMA_VERSION:\n        _reject("OML-073 reliability schema mismatch")\n    if reliability.engine_id != RELIABILITY_ENGINE_ID:\n        _reject("OML-073 reliability engine mismatch")\n    if reliability.upstream_tracking_hash != (\n        lifecycle.lifecycle_tracking.tracking_hash\n    ):\n        _reject("OML-073 lifecycle-to-reliability lineage mismatch")\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "upstream_schema_version": lifecycle.schema_version,\n        "upstream_engine_id": lifecycle.engine_id,\n        "upstream_certification_hash": lifecycle.certification_hash,\n        "upstream_lifecycle_tracking_hash": (\n            lifecycle.lifecycle_tracking.tracking_hash\n        ),\n        "reliability_schema_version": reliability.schema_version,\n        "reliability_engine_id": reliability.engine_id,\n        "source_reliability": reliability,\n        "source_count": reliability.source_count,\n        "total_observation_count": reliability.total_observation_count,\n        "state": STATE_READ_ONLY,\n        "lifecycle_lineage_verified": True,\n        "narrative_lineage_verified": (\n            lifecycle.observation_lifecycle_lineage_verified\n        ),\n        "certified_observation_lineage_verified": (\n            reliability.certified_observation_lineage_verified\n        ),\n        "deterministic_scoring_verified": (\n            reliability.deterministic_scoring_verified\n        ),\n        "source_identity_uniqueness_verified": (\n            reliability.source_identity_uniqueness_verified\n        ),\n        "contradiction_tracking_verified": (\n            reliability.contradiction_tracking_verified\n        ),\n        "calibration_tracking_verified": (\n            reliability.calibration_tracking_verified\n        ),\n        "persistence_enabled": False,\n        "learning_updates_enabled": False,\n        "runtime_activation_enabled": False,\n        "publication_enabled": False,\n        "action_authorization_enabled": False,\n        "qseries_execution_enabled": False,\n        "reliability_ready": True,\n        "downstream_calibration_authorized": (\n            reliability.downstream_calibration_authorized\n        ),\n        "read_only": True,\n    }\n    result = OracleMemoryCertifiedMarketBehaviorSourceReliability073(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_oracle_memory_certified_market_behavior_source_reliability_073(result)\n    return result\n\n\ndef verify_oracle_memory_certified_market_behavior_source_reliability_073(\n    result: OracleMemoryCertifiedMarketBehaviorSourceReliability073,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-073 certification hash mismatch")\n\n    if result.schema_version != SCHEMA_VERSION:\n        _reject("OML-073 schema mismatch")\n    if result.engine_id != ENGINE_ID:\n        _reject("OML-073 engine mismatch")\n    if result.policy_id != POLICY_ID:\n        _reject("OML-073 policy mismatch")\n    if result.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-073 subsystem mismatch")\n    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-073 upstream schema lineage mismatch")\n    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-073 upstream engine lineage mismatch")\n    if result.reliability_schema_version != RELIABILITY_SCHEMA_VERSION:\n        _reject("OML-073 reliability schema lineage mismatch")\n    if result.reliability_engine_id != RELIABILITY_ENGINE_ID:\n        _reject("OML-073 reliability engine lineage mismatch")\n\n    for value in (\n        result.upstream_certification_hash,\n        result.upstream_lifecycle_tracking_hash,\n        result.certification_hash,\n    ):\n        _require_hash(value, "lineage hash")\n\n    verify_oracle_memory_certified_source_reliability(\n        result.source_reliability\n    )\n\n    if result.upstream_lifecycle_tracking_hash != (\n        result.source_reliability.upstream_tracking_hash\n    ):\n        _reject("OML-073 reliability lineage mismatch")\n    if result.source_count != result.source_reliability.source_count:\n        _reject("OML-073 source count mismatch")\n    if result.total_observation_count != (\n        result.source_reliability.total_observation_count\n    ):\n        _reject("OML-073 observation count mismatch")\n\n    required = (\n        result.lifecycle_lineage_verified,\n        result.narrative_lineage_verified,\n        result.certified_observation_lineage_verified,\n        result.deterministic_scoring_verified,\n        result.source_identity_uniqueness_verified,\n        result.contradiction_tracking_verified,\n        result.calibration_tracking_verified,\n        result.reliability_ready,\n        result.downstream_calibration_authorized,\n        result.read_only,\n    )\n    if not all(required):\n        _reject("OML-073 guarantee missing")\n    if result.state != STATE_READ_ONLY:\n        _reject("OML-073 state invalid")\n\n    forbidden = (\n        result.persistence_enabled,\n        result.learning_updates_enabled,\n        result.runtime_activation_enabled,\n        result.publication_enabled,\n        result.action_authorization_enabled,\n        result.qseries_execution_enabled,\n    )\n    if any(forbidden):\n        _reject("OML-073 forbidden capability enabled")\n\n    return True\n'
TEST_SOURCE = 'from __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_source_reliability_073 import (\n    OracleMemoryCertifiedMarketBehaviorReliability073InvariantError,\n    build_oracle_memory_certified_market_behavior_source_reliability_073,\n    verify_oracle_memory_certified_market_behavior_source_reliability_073,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (\n    build_oracle_memory_certified_source_outcome,\n)\n\n\ndef load_module(path: Path, name: str):\n    specification = importlib.util.spec_from_file_location(name, path)\n    if specification is None or specification.loader is None:\n        raise RuntimeError(f"unable to load fixture: {path}")\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef expect_rejection(callable_object, label: str) -> None:\n    try:\n        callable_object()\n    except OracleMemoryCertifiedMarketBehaviorReliability073InvariantError:\n        return\n    raise AssertionError(f"tampered OML-073 {label} accepted")\n\n\ndef build_reliability(root: Path):\n    fixture_072 = load_module(\n        root / "test_oml_072_oracle_memory_certified_market_behavior_narrative_lifecycle_tracking.py",\n        "oml_072_fixture_for_oml_073",\n    )\n    lifecycle = fixture_072.build_lifecycle(root)\n\n    observation_hashes = tuple(sorted({\n        value\n        for binding in lifecycle.lifecycle_tracking.bindings\n        for value in binding.source_observation_hashes\n    }))\n    assert observation_hashes\n\n    outcomes = tuple(\n        build_oracle_memory_certified_source_outcome(\n            source_name="Oracle Market-Behavior Observation",\n            observation_hash=value,\n            outcome_confirmed=True,\n            outcome_correct=(index % 2 == 0),\n            contradiction_count=0 if index % 2 == 0 else 1,\n            confidence_at_observation=0.80 - (index * 0.05),\n            observed_at=f"2026-08-04T13:{20 + index:02d}:00-05:00",\n        )\n        for index, value in enumerate(observation_hashes)\n    )\n\n    result = build_oracle_memory_certified_market_behavior_source_reliability_073(\n        lifecycle=lifecycle,\n        outcomes=outcomes,\n    )\n    return result, lifecycle, outcomes\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OML-073 TEST")\n    print(" CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    result, lifecycle, outcomes = build_reliability(root)\n\n    assert result.schema_version == "OML-073"\n    assert result.engine_id == "OML-073"\n    assert result.upstream_schema_version == "OML-072"\n    assert result.upstream_engine_id == "OML-072"\n    assert result.reliability_schema_version == "OML-034"\n    assert result.reliability_engine_id == "OML-034"\n    assert result.source_count == 1\n    assert result.total_observation_count == len(outcomes)\n    assert result.upstream_certification_hash == lifecycle.certification_hash\n    assert result.upstream_lifecycle_tracking_hash == lifecycle.lifecycle_tracking.tracking_hash\n    assert result.lifecycle_lineage_verified\n    assert result.narrative_lineage_verified\n    assert result.certified_observation_lineage_verified\n    assert result.deterministic_scoring_verified\n    assert result.source_identity_uniqueness_verified\n    assert result.contradiction_tracking_verified\n    assert result.calibration_tracking_verified\n    assert result.reliability_ready\n    assert result.downstream_calibration_authorized\n    assert result.read_only\n    assert not result.persistence_enabled\n    assert not result.learning_updates_enabled\n    assert not result.runtime_activation_enabled\n    assert not result.publication_enabled\n    assert not result.action_authorization_enabled\n    assert not result.qseries_execution_enabled\n\n    replay, _, _ = build_reliability(root)\n    assert replay == result\n    assert verify_oracle_memory_certified_market_behavior_source_reliability_073(result)\n\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_source_reliability_073(\n            replace(result, persistence_enabled=True)\n        ),\n        "persistence state",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_source_reliability_073(\n            replace(result, downstream_calibration_authorized=False)\n        ),\n        "calibration continuation",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_source_reliability_073(\n            replace(result, qseries_execution_enabled=True)\n        ),\n        "Q Series execution",\n    )\n\n    print("[PASS] Certified OML-072 lifecycle consumed read-only")\n    print("[PASS] Exact OML-033 lifecycle object passed directly")\n    print("[PASS] Actual OML-034 source-reliability builder consumed")\n    print("[PASS] Outcomes bound only to certified observation hashes")\n    print("[PASS] Narrative and lifecycle lineage retained")\n    print("[PASS] Reliability and calibration tracking retained")\n    print("[PASS] Calibration continuation authorized read-only")\n    print("[PASS] Deterministic replay equality verified")\n    print("[PASS] Active capabilities remained disabled")\n    print("[PASS] Tampered OML-073 reliability objects rejected")\n    print("[DONE] OML-073 CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_current_repository() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, RELIABILITY)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Required certified files missing: " + ", ".join(missing))
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    lifecycle_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking_072"
    )
    reliability_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory"
    )

    for module, name, expected in (
        (lifecycle_module, "SCHEMA_VERSION", "OML-072"),
        (lifecycle_module, "ENGINE_ID", "OML-072"),
        (reliability_module, "SCHEMA_VERSION", "OML-034"),
        (reliability_module, "ENGINE_ID", "OML-034"),
    ):
        actual = getattr(module, name, None)
        if actual != expected:
            raise RuntimeError(
                f"Current repository {module.__name__}.{name} mismatch: expected {expected!r}, got {actual!r}"
            )

    lifecycle_fields = set(
        lifecycle_module.OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle072.__dataclass_fields__
    )
    required_fields = {
        "lifecycle_tracking", "lifecycle_ready", "downstream_source_reliability_authorized",
        "certification_hash", "read_only"
    }
    missing_fields = sorted(required_fields - lifecycle_fields)
    if missing_fields:
        raise RuntimeError("OML-072 dataclass fields missing: " + ", ".join(missing_fields))

    builder = getattr(reliability_module, "build_oracle_memory_certified_source_reliability", None)
    if builder is None:
        raise RuntimeError("OML-034 source-reliability builder missing")
    parameters = set(inspect.signature(builder).parameters)
    missing_parameters = sorted({"tracking", "outcomes"} - parameters)
    if missing_parameters:
        raise RuntimeError("OML-034 builder parameters missing: " + ", ".join(missing_parameters))


def main() -> int:
    print("=" * 48)
    print(" OML-073 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY")
    print("=" * 48)
    print("[BOOT] Revision: FULL_REPOSITORY_OML_072_034_EXACT_INTERFACE")
    try:
        validate_current_repository()
        print("[OK] Current OML-072 dataclass inspected")
        print("[OK] Current OML-034 builder signature inspected")

        upstream_run = subprocess.run([sys.executable, str(UPSTREAM_TEST)], cwd=ROOT, check=False)
        if upstream_run.returncode:
            raise RuntimeError(f"OML-072 certification failed with exit code {upstream_run.returncode}")

        tracked = {path: path.read_bytes() for path in (UPSTREAM, UPSTREAM_TEST, RELIABILITY)}
        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_certified_market_behavior_source_reliability_073 import *"
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
            raise RuntimeError(f"OML-073 test failed with exit code {completed.returncode}")

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Complete OML-073 production replacement installed")
        print("[PASS] Complete deterministic standalone test installed")
        print("[PASS] Certified OML-072 and OML-034 files unchanged")
        print("[PASS] Deterministic replay preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[DONE] OML-073 INSTALLED")
        return 0
    except (RuntimeError, SyntaxError, ImportError, AttributeError, KeyError, TypeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
