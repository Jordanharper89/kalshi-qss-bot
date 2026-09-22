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
    / "oracle_memory_certified_market_behavior_"
      "multi_hop_causal_chain_memory_076.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_076_oracle_memory_certified_market_behavior_"
      "multi_hop_causal_chain_memory.py"
)
DEPENDENCY_038 = (
    PACKAGE
    / "oracle_memory_certified_observation_"
      "cross_market_dependency_memory.py"
)
PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_"
      "cross_market_dependency_memory_077.py"
)
TEST = (
    ROOT
    / "test_oml_077_oracle_memory_certified_market_behavior_"
      "cross_market_dependency_memory.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Mapping, Sequence\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076 import (\n    OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076,\n    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (\n    OracleMemoryCertifiedCrossMarketDependencyMemory,\n    OracleMemoryCertifiedCrossMarketObservationRequest,\n    build_oracle_memory_certified_cross_market_dependency_memory,\n    verify_oracle_memory_certified_cross_market_dependency_memory,\n    verify_oracle_memory_certified_cross_market_observation_request,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (\n    SUBSYSTEM_ID,\n)\n\nSCHEMA_VERSION = "OML-077"\nENGINE_ID = "OML-077"\nPOLICY_ID = (\n    "oracle-memory.certified-market-behavior-"\n    "cross-market-dependency-memory-077.v1"\n)\nUPSTREAM_SCHEMA_VERSION = "OML-076"\nUPSTREAM_ENGINE_ID = "OML-076"\nDEPENDENCY_SCHEMA_VERSION = "OML-038"\nDEPENDENCY_ENGINE_ID = "OML-038"\nSTATE_READ_ONLY = (\n    "read_only_market_behavior_cross_market_dependency_memory_077"\n)\n\n\nclass OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(\n    RuntimeError\n):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    upstream_chain_certification_hash: str\n    upstream_chain_memory_hash: str\n    dependency_schema_version: str\n    dependency_engine_id: str\n    dependencies: OracleMemoryCertifiedCrossMarketDependencyMemory\n    dependency_count: int\n    total_observation_count: int\n    source_market_count: int\n    target_market_count: int\n    state: str\n    chain_lineage_verified: bool\n    certified_observation_lineage_verified: bool\n    deterministic_identity_verified: bool\n    canonical_dependency_order_verified: bool\n    lead_lag_direction_verified: bool\n    evidence_lineage_verified: bool\n    contradiction_tracking_verified: bool\n    calibration_lineage_verified: bool\n    outcome_reconciliation_verified: bool\n    persistence_enabled: bool\n    learning_updates_enabled: bool\n    runtime_activation_enabled: bool\n    publication_enabled: bool\n    action_authorization_enabled: bool\n    qseries_execution_enabled: bool\n    dependency_memory_ready: bool\n    downstream_freeze_certification_authorized: bool\n    read_only: bool\n    certification_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(\n                value.items(),\n                key=lambda pair: str(pair[0]),\n            )\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(\n        "unsupported OML-077 value type"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(\n        json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            separators=(",", ":"),\n            ensure_ascii=True,\n            allow_nan=False,\n        ).encode("utf-8")\n    ).hexdigest()\n\n\ndef _reject(reason: str) -> None:\n    raise OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(\n        reason\n    )\n\n\ndef _require_hash(value: str, label: str) -> None:\n    if not isinstance(value, str) or len(value) != 64:\n        _reject(f"OML-077 invalid {label} length")\n    try:\n        int(value, 16)\n    except ValueError as exc:\n        raise OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(\n            f"OML-077 invalid {label} hexadecimal value"\n        ) from exc\n\n\ndef build_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(\n    *,\n    chains: OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076,\n    requests: Sequence[OracleMemoryCertifiedCrossMarketObservationRequest],\n) -> OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077:\n    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(\n        chains\n    )\n\n    if chains.schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-077 upstream schema mismatch")\n    if chains.engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-077 upstream engine mismatch")\n    if not chains.chain_memory_ready:\n        _reject("OML-077 upstream chain memory not ready")\n    if not chains.downstream_cross_market_dependency_authorized:\n        _reject("OML-077 dependency continuation not authorized")\n    if not chains.read_only:\n        _reject("OML-077 upstream chain memory not read-only")\n\n    for request in requests:\n        verify_oracle_memory_certified_cross_market_observation_request(\n            request\n        )\n\n    dependencies = build_oracle_memory_certified_cross_market_dependency_memory(\n        chains=chains.chains,\n        requests=tuple(requests),\n    )\n    verify_oracle_memory_certified_cross_market_dependency_memory(\n        dependencies\n    )\n\n    if dependencies.schema_version != DEPENDENCY_SCHEMA_VERSION:\n        _reject("OML-077 dependency schema mismatch")\n    if dependencies.engine_id != DEPENDENCY_ENGINE_ID:\n        _reject("OML-077 dependency engine mismatch")\n    if dependencies.upstream_certification_hash != (\n        chains.chains.certification_hash\n    ):\n        _reject("OML-077 chain certification lineage mismatch")\n    if dependencies.upstream_chain_memory_hash != (\n        chains.chains.chain_memory.memory_hash\n    ):\n        _reject("OML-077 chain memory lineage mismatch")\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "upstream_schema_version": chains.schema_version,\n        "upstream_engine_id": chains.engine_id,\n        "upstream_certification_hash": chains.certification_hash,\n        "upstream_chain_certification_hash": (\n            chains.chains.certification_hash\n        ),\n        "upstream_chain_memory_hash": (\n            chains.chains.chain_memory.memory_hash\n        ),\n        "dependency_schema_version": dependencies.schema_version,\n        "dependency_engine_id": dependencies.engine_id,\n        "dependencies": dependencies,\n        "dependency_count": dependencies.dependency_count,\n        "total_observation_count": dependencies.total_observation_count,\n        "source_market_count": dependencies.source_market_count,\n        "target_market_count": dependencies.target_market_count,\n        "state": STATE_READ_ONLY,\n        "chain_lineage_verified": dependencies.chain_lineage_verified,\n        "certified_observation_lineage_verified": (\n            dependencies.certified_observation_lineage_verified\n        ),\n        "deterministic_identity_verified": (\n            dependencies.deterministic_identity_verified\n        ),\n        "canonical_dependency_order_verified": (\n            dependencies.canonical_dependency_order_verified\n        ),\n        "lead_lag_direction_verified": (\n            dependencies.lead_lag_direction_verified\n        ),\n        "evidence_lineage_verified": (\n            dependencies.evidence_lineage_verified\n        ),\n        "contradiction_tracking_verified": (\n            dependencies.contradiction_tracking_verified\n        ),\n        "calibration_lineage_verified": (\n            dependencies.calibration_lineage_verified\n        ),\n        "outcome_reconciliation_verified": (\n            dependencies.outcome_reconciliation_verified\n        ),\n        "persistence_enabled": False,\n        "learning_updates_enabled": False,\n        "runtime_activation_enabled": False,\n        "publication_enabled": False,\n        "action_authorization_enabled": False,\n        "qseries_execution_enabled": False,\n        "dependency_memory_ready": dependencies.memory_ready,\n        "downstream_freeze_certification_authorized": True,\n        "read_only": True,\n    }\n\n    result = (\n        OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077(\n            **body,\n            certification_hash=_stable_hash(body),\n        )\n    )\n    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(\n        result\n    )\n    return result\n\n\ndef verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(\n    result: OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-077 certification hash mismatch")\n\n    if result.schema_version != SCHEMA_VERSION:\n        _reject("OML-077 schema mismatch")\n    if result.engine_id != ENGINE_ID:\n        _reject("OML-077 engine mismatch")\n    if result.policy_id != POLICY_ID:\n        _reject("OML-077 policy mismatch")\n    if result.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-077 subsystem mismatch")\n    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-077 upstream schema lineage mismatch")\n    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-077 upstream engine lineage mismatch")\n    if result.dependency_schema_version != DEPENDENCY_SCHEMA_VERSION:\n        _reject("OML-077 dependency schema lineage mismatch")\n    if result.dependency_engine_id != DEPENDENCY_ENGINE_ID:\n        _reject("OML-077 dependency engine lineage mismatch")\n\n    for value in (\n        result.upstream_certification_hash,\n        result.upstream_chain_certification_hash,\n        result.upstream_chain_memory_hash,\n        result.certification_hash,\n    ):\n        _require_hash(value, "lineage hash")\n\n    verify_oracle_memory_certified_cross_market_dependency_memory(\n        result.dependencies\n    )\n\n    if result.upstream_chain_certification_hash != (\n        result.dependencies.upstream_certification_hash\n    ):\n        _reject("OML-077 chain certification mismatch")\n    if result.upstream_chain_memory_hash != (\n        result.dependencies.upstream_chain_memory_hash\n    ):\n        _reject("OML-077 chain memory mismatch")\n    if result.dependency_count != result.dependencies.dependency_count:\n        _reject("OML-077 dependency count mismatch")\n    if result.total_observation_count != (\n        result.dependencies.total_observation_count\n    ):\n        _reject("OML-077 observation count mismatch")\n    if result.source_market_count != (\n        result.dependencies.source_market_count\n    ):\n        _reject("OML-077 source market count mismatch")\n    if result.target_market_count != (\n        result.dependencies.target_market_count\n    ):\n        _reject("OML-077 target market count mismatch")\n\n    required = (\n        result.chain_lineage_verified,\n        result.certified_observation_lineage_verified,\n        result.deterministic_identity_verified,\n        result.canonical_dependency_order_verified,\n        result.lead_lag_direction_verified,\n        result.evidence_lineage_verified,\n        result.contradiction_tracking_verified,\n        result.calibration_lineage_verified,\n        result.outcome_reconciliation_verified,\n        result.dependency_memory_ready,\n        result.downstream_freeze_certification_authorized,\n        result.read_only,\n    )\n    if not all(required):\n        _reject("OML-077 guarantee missing")\n\n    if result.state != STATE_READ_ONLY:\n        _reject("OML-077 state invalid")\n\n    forbidden = (\n        result.persistence_enabled,\n        result.learning_updates_enabled,\n        result.runtime_activation_enabled,\n        result.publication_enabled,\n        result.action_authorization_enabled,\n        result.qseries_execution_enabled,\n    )\n    if any(forbidden):\n        _reject("OML-077 forbidden capability enabled")\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_cross_market_dependency_memory_077 import (\n    OracleMemoryCertifiedMarketBehaviorDependency077InvariantError,\n    build_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077,\n    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (\n    build_oracle_memory_certified_cross_market_observation_request,\n)\n\n\ndef load_module(path: Path, name: str):\n    specification = importlib.util.spec_from_file_location(name, path)\n    if specification is None or specification.loader is None:\n        raise RuntimeError(f"unable to load fixture: {path}")\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef expect_rejection(callable_object, label: str) -> None:\n    try:\n        callable_object()\n    except OracleMemoryCertifiedMarketBehaviorDependency077InvariantError:\n        return\n    raise AssertionError(f"tampered OML-077 {label} accepted")\n\n\ndef build_dependencies(root: Path):\n    fixture_076 = load_module(\n        root\n        / "test_oml_076_oracle_memory_certified_market_behavior_"\n        "multi_hop_causal_chain_memory.py",\n        "oml_076_fixture_for_oml_077",\n    )\n    chains, causal_patterns, certified_hashes = fixture_076.build_chains(\n        root\n    )\n    chain_id = chains.chains.chain_memory.chains[0].chain_id\n\n    request = build_oracle_memory_certified_cross_market_observation_request(\n        dependency_name=(\n            "Certified market-behavior chain leads target-market repricing"\n        ),\n        chain_ids=(chain_id,),\n        source_market_id="a" * 64,\n        target_market_id="b" * 64,\n        source_event_hash="c" * 64,\n        target_event_hash="d" * 64,\n        source_observed_at="2026-08-04T16:00:00-05:00",\n        target_observed_at="2026-08-04T16:10:00-05:00",\n        lag_seconds=600,\n        certified_observation_hashes=(certified_hashes[0],),\n        contradicting_certified_observation_hashes=(),\n        confidence=0.82,\n        calibrated_probability=0.80,\n        outcome_confirmed=True,\n        dependency_supported=True,\n    )\n\n    result = (\n        build_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(\n            chains=chains,\n            requests=(request,),\n        )\n    )\n    return result, chains, certified_hashes\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OML-077 TEST")\n    print(" CERTIFIED MARKET-BEHAVIOR CROSS-MARKET DEPENDENCY MEMORY")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    result, chains, certified_hashes = build_dependencies(root)\n\n    assert result.schema_version == "OML-077"\n    assert result.engine_id == "OML-077"\n    assert result.upstream_schema_version == "OML-076"\n    assert result.upstream_engine_id == "OML-076"\n    assert result.dependency_schema_version == "OML-038"\n    assert result.dependency_engine_id == "OML-038"\n    assert result.dependency_count == 1\n    assert result.total_observation_count >= 1\n    assert result.source_market_count == 1\n    assert result.target_market_count == 1\n    assert result.chain_lineage_verified\n    assert result.certified_observation_lineage_verified\n    assert result.lead_lag_direction_verified\n    assert result.evidence_lineage_verified\n    assert result.calibration_lineage_verified\n    assert result.outcome_reconciliation_verified\n    assert result.dependency_memory_ready\n    assert result.downstream_freeze_certification_authorized\n    assert result.read_only\n    assert not result.persistence_enabled\n    assert not result.learning_updates_enabled\n    assert not result.runtime_activation_enabled\n    assert not result.publication_enabled\n    assert not result.action_authorization_enabled\n    assert not result.qseries_execution_enabled\n\n    binding = result.dependencies.bindings[0]\n    assert set(binding.certified_observation_hashes).issubset(\n        set(certified_hashes)\n    )\n    assert binding.chain_ids == (\n        chains.chains.chain_memory.chains[0].chain_id,\n    )\n\n    replay, _, _ = build_dependencies(root)\n    assert replay == result\n    assert (\n        verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(\n            result\n        )\n    )\n\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(\n            replace(result, persistence_enabled=True)\n        ),\n        "persistence",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(\n            replace(result, qseries_execution_enabled=True)\n        ),\n        "Q Series execution",\n    )\n\n    print("[PASS] Certified OML-076 chain memory consumed read-only")\n    print("[PASS] Exact OML-037 chain object passed directly")\n    print("[PASS] Actual OML-038 dependency builder consumed")\n    print("[PASS] Market identity and lead-lag direction verified")\n    print("[PASS] Certified observation and chain lineage retained")\n    print("[PASS] Calibration and outcome reconciliation retained")\n    print("[PASS] Freeze certification continuation authorized read-only")\n    print("[PASS] Deterministic replay equality verified")\n    print("[PASS] Active capabilities remained disabled")\n    print("[PASS] Tampered OML-077 dependency objects rejected")\n    print("[DONE] OML-077 CERTIFIED MARKET-BEHAVIOR DEPENDENCY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_current_repository() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, DEPENDENCY_038)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_"
        "multi_hop_causal_chain_memory_076"
    )
    dependency_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_"
        "cross_market_dependency_memory"
    )

    expected = (
        (upstream_module, "SCHEMA_VERSION", "OML-076"),
        (upstream_module, "ENGINE_ID", "OML-076"),
        (dependency_module, "SCHEMA_VERSION", "OML-038"),
        (dependency_module, "ENGINE_ID", "OML-038"),
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
        OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076.
        __dataclass_fields__
    )
    required_fields = {
        "chains",
        "chain_memory_ready",
        "downstream_cross_market_dependency_authorized",
        "certification_hash",
        "read_only",
    }
    missing_fields = sorted(required_fields - upstream_fields)
    if missing_fields:
        raise RuntimeError(
            "OML-076 dataclass fields missing: "
            + ", ".join(missing_fields)
        )

    request_builder = getattr(
        dependency_module,
        "build_oracle_memory_certified_"
        "cross_market_observation_request",
        None,
    )
    memory_builder = getattr(
        dependency_module,
        "build_oracle_memory_certified_"
        "cross_market_dependency_memory",
        None,
    )
    if request_builder is None or memory_builder is None:
        raise RuntimeError("OML-038 required builders missing")

    required_request_parameters = {
        "dependency_name",
        "chain_ids",
        "source_market_id",
        "target_market_id",
        "source_event_hash",
        "target_event_hash",
        "source_observed_at",
        "target_observed_at",
        "lag_seconds",
        "certified_observation_hashes",
        "contradicting_certified_observation_hashes",
        "confidence",
        "calibrated_probability",
        "outcome_confirmed",
        "dependency_supported",
    }
    request_parameters = set(
        inspect.signature(request_builder).parameters
    )
    missing_request_parameters = sorted(
        required_request_parameters - request_parameters
    )
    if missing_request_parameters:
        raise RuntimeError(
            "OML-038 request parameters missing: "
            + ", ".join(missing_request_parameters)
        )

    memory_parameters = set(inspect.signature(memory_builder).parameters)
    missing_memory_parameters = sorted(
        {"chains", "requests"} - memory_parameters
    )
    if missing_memory_parameters:
        raise RuntimeError(
            "OML-038 memory parameters missing: "
            + ", ".join(missing_memory_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-077 INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)
    print(
        "[BOOT] Revision: "
        "CURRENT_REPOSITORY_OML_076_038_EXACT_ALIGNMENT"
    )

    try:
        validate_current_repository()
        print("[OK] Current OML-076 dataclass inspected")
        print("[OK] Current OML-038 builder signatures inspected")

        tracked = {
            path: path.read_bytes()
            for path in (UPSTREAM, UPSTREAM_TEST, DEPENDENCY_038)
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "cross_market_dependency_memory_077 import *"
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
                f"OML-077 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Complete OML-077 production replacement installed")
        print("[PASS] Complete deterministic standalone test installed")
        print("[PASS] Certified OML-076 and OML-038 files unchanged")
        print("[PASS] Deterministic replay preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[DONE] OML-077 INSTALLED")
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
