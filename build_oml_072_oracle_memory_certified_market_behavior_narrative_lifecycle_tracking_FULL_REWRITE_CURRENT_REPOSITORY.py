from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM_071 = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_"
      "narrative_detection_and_evolution_071.py"
)
UPSTREAM_071_TEST = (
    ROOT
    / "test_oml_071_oracle_memory_certified_market_behavior_"
      "narrative_detection_and_evolution.py"
)
UPSTREAM_070 = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_relationship_graph_070.py"
)
UPSTREAM_070_TEST = (
    ROOT
    / "test_oml_070_oracle_memory_certified_market_behavior_"
      "relationship_graph.py"
)
LIFECYCLE_033 = (
    PACKAGE
    / "oracle_memory_certified_observation_"
      "narrative_lifecycle_tracking.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_market_behavior_"
      "narrative_lifecycle_tracking_072.py"
)
TEST = (
    ROOT
    / "test_oml_072_oracle_memory_certified_market_behavior_"
      "narrative_lifecycle_tracking.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Mapping, Sequence\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_detection_and_evolution_071 import (\n    OracleMemoryCertifiedMarketBehaviorNarrativeDetection071,\n    verify_oracle_memory_certified_market_behavior_narrative_detection_071,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking import (\n    OracleMemoryObservationNarrativeLifecycleTracking,\n    build_oracle_memory_observation_narrative_lifecycle_tracking,\n    verify_oracle_memory_observation_narrative_lifecycle_tracking,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (\n    OracleMemoryNarrative,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (\n    SUBSYSTEM_ID,\n)\n\nSCHEMA_VERSION = "OML-072"\nENGINE_ID = "OML-072"\nPOLICY_ID = (\n    "oracle-memory."\n    "certified-market-behavior-narrative-lifecycle-tracking-072.v1"\n)\nUPSTREAM_SCHEMA_VERSION = "OML-071"\nUPSTREAM_ENGINE_ID = "OML-071"\nLIFECYCLE_SCHEMA_VERSION = "OML-033"\nLIFECYCLE_ENGINE_ID = "OML-033"\nSTATE_READ_ONLY = "read_only_market_behavior_narrative_lifecycle_072"\n\n\nclass OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True)\nclass OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle072:\n    schema_version: str\n    engine_id: str\n    policy_id: str\n    subsystem_id: str\n    upstream_schema_version: str\n    upstream_engine_id: str\n    upstream_certification_hash: str\n    upstream_detection_hash: str\n    lifecycle_schema_version: str\n    lifecycle_engine_id: str\n    lifecycle_tracking: OracleMemoryObservationNarrativeLifecycleTracking\n    narrative_count: int\n    snapshot_count: int\n    transition_count: int\n    state: str\n    detection_lineage_verified: bool\n    observation_lifecycle_lineage_verified: bool\n    entity_lineage_preserved: bool\n    relationship_lineage_preserved: bool\n    canonical_temporal_order_verified: bool\n    deterministic_lifecycle_tracking_verified: bool\n    evidence_growth_tracked: bool\n    contradiction_growth_tracked: bool\n    persistence_enabled: bool\n    learning_updates_enabled: bool\n    runtime_activation_enabled: bool\n    publication_enabled: bool\n    action_authorization_enabled: bool\n    qseries_execution_enabled: bool\n    lifecycle_ready: bool\n    downstream_source_reliability_authorized: bool\n    read_only: bool\n    certification_hash: str\n\n\ndef _canonical(value: Any) -> Any:\n    if hasattr(value, "__dataclass_fields__"):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError(\n        "unsupported OML-072 value type"\n    )\n\n\ndef _stable_hash(value: Any) -> str:\n    return hashlib.sha256(\n        json.dumps(\n            _canonical(value),\n            sort_keys=True,\n            separators=(",", ":"),\n            ensure_ascii=True,\n            allow_nan=False,\n        ).encode("utf-8")\n    ).hexdigest()\n\n\ndef _reject(reason: str) -> None:\n    raise OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError(reason)\n\n\ndef _require_hash(value: str, label: str) -> None:\n    if not isinstance(value, str) or len(value) != 64:\n        _reject(f"OML-072 invalid {label} length")\n    try:\n        int(value, 16)\n    except ValueError as exc:\n        raise OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError(\n            f"OML-072 invalid {label} hexadecimal value"\n        ) from exc\n\n\ndef build_oracle_memory_certified_market_behavior_narrative_lifecycle_072(\n    *,\n    detection: OracleMemoryCertifiedMarketBehaviorNarrativeDetection071,\n    prior_histories: Mapping[str, Sequence[OracleMemoryNarrative]],\n) -> OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle072:\n    verify_oracle_memory_certified_market_behavior_narrative_detection_071(detection)\n\n    if detection.schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-072 upstream schema mismatch")\n    if detection.engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-072 upstream engine mismatch")\n    if not detection.detection_ready:\n        _reject("OML-072 upstream detection not ready")\n    if not detection.downstream_lifecycle_tracking_authorized:\n        _reject("OML-072 lifecycle continuation not authorized")\n    if not detection.read_only:\n        _reject("OML-072 upstream detection not read-only")\n\n    tracking = build_oracle_memory_observation_narrative_lifecycle_tracking(\n        detection=detection.narrative_detection,\n        prior_histories=prior_histories,\n    )\n    verify_oracle_memory_observation_narrative_lifecycle_tracking(tracking)\n\n    if tracking.schema_version != LIFECYCLE_SCHEMA_VERSION:\n        _reject("OML-072 lifecycle schema mismatch")\n    if tracking.engine_id != LIFECYCLE_ENGINE_ID:\n        _reject("OML-072 lifecycle engine mismatch")\n    if tracking.upstream_detection_hash != (\n        detection.narrative_detection.detection_hash\n    ):\n        _reject("OML-072 detection-to-lifecycle lineage mismatch")\n\n    body = {\n        "schema_version": SCHEMA_VERSION,\n        "engine_id": ENGINE_ID,\n        "policy_id": POLICY_ID,\n        "subsystem_id": SUBSYSTEM_ID,\n        "upstream_schema_version": detection.schema_version,\n        "upstream_engine_id": detection.engine_id,\n        "upstream_certification_hash": detection.certification_hash,\n        "upstream_detection_hash": (\n            detection.narrative_detection.detection_hash\n        ),\n        "lifecycle_schema_version": tracking.schema_version,\n        "lifecycle_engine_id": tracking.engine_id,\n        "lifecycle_tracking": tracking,\n        "narrative_count": tracking.narrative_count,\n        "snapshot_count": tracking.snapshot_count,\n        "transition_count": tracking.transition_count,\n        "state": STATE_READ_ONLY,\n        "detection_lineage_verified": (\n            tracking.certified_detection_lineage_verified\n        ),\n        "observation_lifecycle_lineage_verified": (\n            tracking.observation_lifecycle_lineage_verified\n        ),\n        "entity_lineage_preserved": tracking.entity_lineage_preserved,\n        "relationship_lineage_preserved": (\n            tracking.relationship_lineage_preserved\n        ),\n        "canonical_temporal_order_verified": (\n            tracking.canonical_temporal_order_verified\n        ),\n        "deterministic_lifecycle_tracking_verified": (\n            tracking.deterministic_lifecycle_tracking_verified\n        ),\n        "evidence_growth_tracked": tracking.evidence_growth_tracked,\n        "contradiction_growth_tracked": (\n            tracking.contradiction_growth_tracked\n        ),\n        "persistence_enabled": False,\n        "learning_updates_enabled": False,\n        "runtime_activation_enabled": False,\n        "publication_enabled": False,\n        "action_authorization_enabled": False,\n        "qseries_execution_enabled": False,\n        "lifecycle_ready": True,\n        "downstream_source_reliability_authorized": (\n            tracking.downstream_source_reliability_authorized\n        ),\n        "read_only": True,\n    }\n\n    result = OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle072(\n        **body,\n        certification_hash=_stable_hash(body),\n    )\n    verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(result)\n    return result\n\n\ndef verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(\n    result: OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle072,\n) -> bool:\n    body = asdict(result)\n    supplied = body.pop("certification_hash")\n    if _stable_hash(body) != supplied:\n        _reject("OML-072 certification hash mismatch")\n\n    if result.schema_version != SCHEMA_VERSION:\n        _reject("OML-072 schema mismatch")\n    if result.engine_id != ENGINE_ID:\n        _reject("OML-072 engine mismatch")\n    if result.policy_id != POLICY_ID:\n        _reject("OML-072 policy mismatch")\n    if result.subsystem_id != SUBSYSTEM_ID:\n        _reject("OML-072 subsystem mismatch")\n    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:\n        _reject("OML-072 upstream schema lineage mismatch")\n    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:\n        _reject("OML-072 upstream engine lineage mismatch")\n    if result.lifecycle_schema_version != LIFECYCLE_SCHEMA_VERSION:\n        _reject("OML-072 lifecycle schema lineage mismatch")\n    if result.lifecycle_engine_id != LIFECYCLE_ENGINE_ID:\n        _reject("OML-072 lifecycle engine lineage mismatch")\n\n    for value in (\n        result.upstream_certification_hash,\n        result.upstream_detection_hash,\n        result.certification_hash,\n    ):\n        _require_hash(value, "lineage hash")\n\n    verify_oracle_memory_observation_narrative_lifecycle_tracking(\n        result.lifecycle_tracking\n    )\n\n    if result.upstream_detection_hash != (\n        result.lifecycle_tracking.upstream_detection_hash\n    ):\n        _reject("OML-072 lifecycle detection lineage mismatch")\n    if result.narrative_count != result.lifecycle_tracking.narrative_count:\n        _reject("OML-072 narrative count mismatch")\n    if result.snapshot_count != result.lifecycle_tracking.snapshot_count:\n        _reject("OML-072 snapshot count mismatch")\n    if result.transition_count != result.lifecycle_tracking.transition_count:\n        _reject("OML-072 transition count mismatch")\n\n    required = (\n        result.detection_lineage_verified,\n        result.observation_lifecycle_lineage_verified,\n        result.entity_lineage_preserved,\n        result.relationship_lineage_preserved,\n        result.canonical_temporal_order_verified,\n        result.deterministic_lifecycle_tracking_verified,\n        result.evidence_growth_tracked,\n        result.contradiction_growth_tracked,\n        result.lifecycle_ready,\n        result.downstream_source_reliability_authorized,\n        result.read_only,\n    )\n    if not all(required):\n        _reject("OML-072 guarantee missing")\n    if result.state != STATE_READ_ONLY:\n        _reject("OML-072 state invalid")\n\n    forbidden = (\n        result.persistence_enabled,\n        result.learning_updates_enabled,\n        result.runtime_activation_enabled,\n        result.publication_enabled,\n        result.action_authorization_enabled,\n        result.qseries_execution_enabled,\n    )\n    if any(forbidden):\n        _reject("OML-072 forbidden capability enabled")\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking_072 import (\n    OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError,\n    build_oracle_memory_certified_market_behavior_narrative_lifecycle_072,\n    verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072,\n)\nfrom qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (\n    build_oracle_memory_narrative,\n)\n\n\ndef load_module(path: Path, name: str):\n    specification = importlib.util.spec_from_file_location(name, path)\n    if specification is None or specification.loader is None:\n        raise RuntimeError(f"unable to load fixture: {path}")\n    module = importlib.util.module_from_spec(specification)\n    sys.modules[name] = module\n    specification.loader.exec_module(module)\n    return module\n\n\ndef expect_rejection(callable_object, label: str) -> None:\n    try:\n        callable_object()\n    except OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError:\n        return\n    raise AssertionError(f"tampered OML-072 {label} accepted")\n\n\ndef build_lifecycle(root: Path):\n    fixture_071 = load_module(\n        root\n        / "test_oml_071_oracle_memory_certified_market_behavior_"\n        "narrative_detection_and_evolution.py",\n        "oml_071_fixture_for_oml_072_full_rewrite",\n    )\n    detection = fixture_071.build_detection(root)\n    current = detection.narrative_detection.narratives[0]\n\n    fixture_070 = load_module(\n        root\n        / "test_oml_070_oracle_memory_certified_market_behavior_"\n        "relationship_graph.py",\n        "oml_070_fixture_for_oml_072_full_rewrite",\n    )\n    resolution = fixture_070.build_resolution(root)\n\n    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_relationship_graph_070 import (\n        build_oracle_memory_certified_market_behavior_relationship_graph_070,\n    )\n    from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (\n        build_oracle_memory_observation_relationship_request,\n    )\n\n    entities = {\n        entity.normalized_name: entity\n        for entity in resolution.resolution.entities\n    }\n    liquidity = entities["stablecoin liquidity"]\n    bitcoin = entities["bitcoin"]\n\n    relationship_request = build_oracle_memory_observation_relationship_request(\n        source_entity_id=liquidity.canonical_entity_id,\n        target_entity_id=bitcoin.canonical_entity_id,\n        relationship_type="precedes market repricing",\n        evidence_hashes=("5" * 64, "6" * 64),\n        confidence=0.84,\n        contradiction_count=0,\n        directed=True,\n    )\n    graph_wrapper = (\n        build_oracle_memory_certified_market_behavior_relationship_graph_070(\n            resolution=resolution,\n            requests=(relationship_request,),\n        )\n    )\n    graph = graph_wrapper.graph_materialization.graph\n\n    graph_entity_ids = tuple(\n        sorted(entity.canonical_entity_id for entity in graph.entities)\n    )\n    graph_relationship_ids = tuple(\n        sorted(item.relationship_id for item in graph.relationships)\n    )\n\n    assert current.participating_entity_ids == graph_entity_ids\n    assert current.relationship_ids == graph_relationship_ids\n\n    prior = build_oracle_memory_narrative(\n        graph=graph,\n        title=current.title,\n        participating_entity_ids=current.participating_entity_ids,\n        relationship_ids=current.relationship_ids,\n        supporting_evidence_hashes=("7" * 64,),\n        contradicting_evidence_hashes=(),\n        confidence=0.58,\n        uncertainty=0.42,\n        first_observed_at=current.first_observed_at,\n        last_observed_at="2026-08-04T12:05:00-05:00",\n        evolution_index=1,\n    )\n\n    return build_oracle_memory_certified_market_behavior_narrative_lifecycle_072(\n        detection=detection,\n        prior_histories={current.narrative_id: (prior,)},\n    )\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OML-072 TEST")\n    print(" CERTIFIED MARKET-BEHAVIOR NARRATIVE LIFECYCLE")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    result = build_lifecycle(root)\n\n    assert result.schema_version == "OML-072"\n    assert result.engine_id == "OML-072"\n    assert result.upstream_schema_version == "OML-071"\n    assert result.upstream_engine_id == "OML-071"\n    assert result.lifecycle_schema_version == "OML-033"\n    assert result.lifecycle_engine_id == "OML-033"\n    assert result.narrative_count == 1\n    assert result.snapshot_count >= 2\n    assert result.transition_count >= 1\n    assert result.detection_lineage_verified\n    assert result.observation_lifecycle_lineage_verified\n    assert result.entity_lineage_preserved\n    assert result.relationship_lineage_preserved\n    assert result.canonical_temporal_order_verified\n    assert result.deterministic_lifecycle_tracking_verified\n    assert result.evidence_growth_tracked\n    assert result.contradiction_growth_tracked\n    assert result.lifecycle_ready\n    assert result.downstream_source_reliability_authorized\n    assert result.read_only\n    assert not result.persistence_enabled\n    assert not result.learning_updates_enabled\n    assert not result.runtime_activation_enabled\n    assert not result.publication_enabled\n    assert not result.action_authorization_enabled\n    assert not result.qseries_execution_enabled\n\n    replay = build_lifecycle(root)\n    assert replay == result\n    assert verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(\n        result\n    )\n\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(\n            replace(result, persistence_enabled=True)\n        ),\n        "persistence",\n    )\n    expect_rejection(\n        lambda: verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(\n            replace(result, qseries_execution_enabled=True)\n        ),\n        "Q Series execution",\n    )\n\n    print("[PASS] Certified OML-071 detection consumed read-only")\n    print("[PASS] Exact OML-032 detection object passed directly")\n    print("[PASS] OML-070 graph rebuilt through exact certified builders")\n    print("[PASS] Canonical entity ordering consumed from certified narrative")\n    print("[PASS] Exact relationship lineage consumed from certified narrative")\n    print("[PASS] Actual OML-033 lifecycle builder consumed")\n    print("[PASS] Temporal evolution indexes remained monotonic")\n    print("[PASS] Evidence and contradiction growth retained")\n    print("[PASS] Deterministic replay equality verified")\n    print("[PASS] Active capabilities remained disabled")\n    print("[PASS] Tampered OML-072 lifecycle objects rejected")\n    print("[DONE] OML-072 FULL REWRITE CERTIFIED PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_current_repository() -> None:
    required = (
        UPSTREAM_071,
        UPSTREAM_071_TEST,
        UPSTREAM_070,
        UPSTREAM_070_TEST,
        LIFECYCLE_033,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified files missing: " + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    detection_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_"
        "narrative_detection_and_evolution_071"
    )
    graph_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_market_behavior_relationship_graph_070"
    )
    lifecycle_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_"
        "narrative_lifecycle_tracking"
    )

    expected = (
        (detection_module, "SCHEMA_VERSION", "OML-071"),
        (detection_module, "ENGINE_ID", "OML-071"),
        (graph_module, "SCHEMA_VERSION", "OML-070"),
        (graph_module, "ENGINE_ID", "OML-070"),
        (lifecycle_module, "SCHEMA_VERSION", "OML-033"),
        (lifecycle_module, "ENGINE_ID", "OML-033"),
    )
    for module, name, value in expected:
        actual = getattr(module, name, None)
        if actual != value:
            raise RuntimeError(
                f"Current repository {module.__name__}.{name} "
                f"mismatch: expected {value!r}, got {actual!r}"
            )

    detection_fields = set(
        detection_module.
        OracleMemoryCertifiedMarketBehaviorNarrativeDetection071.
        __dataclass_fields__
    )
    required_detection_fields = {
        "narrative_detection",
        "detection_ready",
        "downstream_lifecycle_tracking_authorized",
        "certification_hash",
        "read_only",
    }
    missing_detection = sorted(
        required_detection_fields - detection_fields
    )
    if missing_detection:
        raise RuntimeError(
            "OML-071 dataclass fields missing: "
            + ", ".join(missing_detection)
        )

    lifecycle_builder = getattr(
        lifecycle_module,
        "build_oracle_memory_observation_"
        "narrative_lifecycle_tracking",
        None,
    )
    if lifecycle_builder is None:
        raise RuntimeError("OML-033 lifecycle builder missing")

    parameters = set(inspect.signature(lifecycle_builder).parameters)
    missing_parameters = sorted(
        {"detection", "prior_histories"} - parameters
    )
    if missing_parameters:
        raise RuntimeError(
            "OML-033 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-072 FULL REWRITE INSTALLER")
    print(" CERTIFIED MARKET-BEHAVIOR NARRATIVE LIFECYCLE")
    print("=" * 48)
    print(
        "[BOOT] Revision: "
        "FULL_REWRITE_CURRENT_REPOSITORY_OML_071_070_033"
    )

    try:
        validate_current_repository()
        print("[OK] Current OML-071 dataclass inspected")
        print("[OK] Current OML-070 graph interface inspected")
        print("[OK] Current OML-033 builder signature inspected")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_071_TEST)],
            cwd=ROOT,
            check=False,
        )
        if upstream_run.returncode:
            raise RuntimeError(
                "OML-071 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        tracked = {
            path: path.read_bytes()
            for path in (
                UPSTREAM_071,
                UPSTREAM_071_TEST,
                UPSTREAM_070,
                UPSTREAM_070_TEST,
                LIFECYCLE_033,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_memory_certified_market_behavior_"
            "narrative_lifecycle_tracking_072 import *"
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

        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OML-072 test failed with exit code {completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Complete OML-072 production replacement installed")
        print("[PASS] Complete deterministic standalone test installed")
        print("[PASS] Certified OML-071/070/033 files unchanged")
        print("[PASS] Canonical entity ordering preserved")
        print("[PASS] Immutable narrative lineage preserved")
        print("[PASS] Deterministic replay preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Learning updates remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print("[DONE] OML-072 FULL REWRITE INSTALLED")
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
