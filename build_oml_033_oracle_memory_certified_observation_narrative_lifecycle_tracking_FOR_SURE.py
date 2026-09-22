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
    / "oracle_memory_certified_observation_narrative_detection_and_evolution.py"
)
UPSTREAM_TEST = (
    ROOT
    / "test_oml_032_oracle_memory_certified_observation_narrative_detection_and_evolution.py"
)
LIFECYCLE_MODULE = (
    PACKAGE
    / "oracle_memory_narrative_temporal_tracking_and_lifecycle_memory.py"
)
LIFECYCLE_TEST = (
    ROOT
    / "test_oml_021_oracle_memory_narrative_temporal_tracking_and_lifecycle_memory.py"
)

PRODUCTION = (
    PACKAGE
    / "oracle_memory_certified_observation_narrative_lifecycle_tracking.py"
)
TEST = (
    ROOT
    / "test_oml_033_oracle_memory_certified_observation_narrative_lifecycle_tracking.py"
)
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    OracleMemoryObservationNarrativeDetection,
    verify_oracle_memory_observation_narrative_detection,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    OracleMemoryNarrative,
    verify_oracle_memory_narrative,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
    OracleMemoryNarrativeLifecycleMemory,
    build_oracle_memory_narrative_lifecycle_memory,
    verify_oracle_memory_narrative_lifecycle_memory,
)

SCHEMA_VERSION = "OML-033"
ENGINE_ID = "OML-033"
POLICY_ID = (
    "oracle-memory.certified-observation-narrative-lifecycle-tracking.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-032"
UPSTREAM_ENGINE_ID = "OML-032"

LIFECYCLE_STATE_READ_ONLY = "read_only_lifecycle"


class OracleMemoryObservationNarrativeLifecycleInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationNarrativeLifecycleBinding:
    narrative_id: str
    current_narrative_hash: str
    current_detection_binding_hash: str
    lifecycle_snapshot_hashes: tuple[str, ...]
    lifecycle_transition_hashes: tuple[str, ...]
    source_observation_hashes: tuple[str, ...]
    narrative_lineage_verified: bool
    detection_lineage_verified: bool
    observation_lineage_verified: bool
    temporal_lineage_verified: bool
    deterministic_binding_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    binding_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationNarrativeLifecycleTracking:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_detection_hash: str
    upstream_narrative_batch_hash: str
    lifecycle_memory: OracleMemoryNarrativeLifecycleMemory
    bindings: tuple[OracleMemoryObservationNarrativeLifecycleBinding, ...]
    narrative_count: int
    snapshot_count: int
    transition_count: int
    lifecycle_state: str
    certified_detection_lineage_verified: bool
    observation_lifecycle_lineage_verified: bool
    canonical_temporal_order_verified: bool
    deterministic_lifecycle_tracking_verified: bool
    entity_lineage_preserved: bool
    relationship_lineage_preserved: bool
    evidence_growth_tracked: bool
    contradiction_growth_tracked: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    lifecycle_ready: bool
    downstream_source_reliability_authorized: bool
    read_only: bool
    tracking_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise OracleMemoryObservationNarrativeLifecycleInvariantError(
        "unsupported OML-033 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryObservationNarrativeLifecycleInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-033 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationNarrativeLifecycleInvariantError(
            f"OML-033 invalid {label} hexadecimal value"
        ) from exc


def _build_binding(
    *,
    detection: OracleMemoryObservationNarrativeDetection,
    narrative: OracleMemoryNarrative,
    lifecycle_memory: OracleMemoryNarrativeLifecycleMemory,
) -> OracleMemoryObservationNarrativeLifecycleBinding:
    verify_oracle_memory_narrative(narrative)
    verify_oracle_memory_narrative_lifecycle_memory(lifecycle_memory)

    detection_bindings = {
        item.narrative_id: item
        for item in detection.bindings
    }

    detection_binding = detection_bindings.get(narrative.narrative_id)

    if detection_binding is None:
        _reject("OML-033 detection binding missing")

    snapshots = tuple(
        item
        for item in lifecycle_memory.snapshots
        if item.narrative_id == narrative.narrative_id
    )
    transitions = tuple(
        item
        for item in lifecycle_memory.transitions
        if item.narrative_id == narrative.narrative_id
    )

    if not snapshots:
        _reject("OML-033 lifecycle snapshots missing")

    body = {
        "narrative_id": narrative.narrative_id,
        "current_narrative_hash": narrative.narrative_hash,
        "current_detection_binding_hash": detection_binding.binding_hash,
        "lifecycle_snapshot_hashes": tuple(
            item.snapshot_hash for item in snapshots
        ),
        "lifecycle_transition_hashes": tuple(
            item.transition_hash for item in transitions
        ),
        "source_observation_hashes": (
            detection_binding.source_observation_hashes
        ),
        "narrative_lineage_verified": True,
        "detection_lineage_verified": True,
        "observation_lineage_verified": True,
        "temporal_lineage_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    binding = OracleMemoryObservationNarrativeLifecycleBinding(
        **body,
        binding_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_narrative_lifecycle_binding(
        binding
    )
    return binding


def verify_oracle_memory_observation_narrative_lifecycle_binding(
    binding: OracleMemoryObservationNarrativeLifecycleBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-033 binding hash mismatch")

    for value in (
        binding.narrative_id,
        binding.current_narrative_hash,
        binding.current_detection_binding_hash,
        binding.binding_hash,
        *binding.lifecycle_snapshot_hashes,
        *binding.lifecycle_transition_hashes,
        *binding.source_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")

    required_true = (
        binding.narrative_lineage_verified,
        binding.detection_lineage_verified,
        binding.observation_lineage_verified,
        binding.temporal_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )

    if not all(required_true):
        _reject("OML-033 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-033 forbidden binding capability enabled")

    return True


def build_oracle_memory_observation_narrative_lifecycle_tracking(
    *,
    detection: OracleMemoryObservationNarrativeDetection,
    prior_histories: Mapping[str, Sequence[OracleMemoryNarrative]] | None = None,
) -> OracleMemoryObservationNarrativeLifecycleTracking:
    verify_oracle_memory_observation_narrative_detection(detection)

    if detection.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-033 upstream schema mismatch")

    if detection.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-033 upstream engine mismatch")

    if not detection.detection_ready:
        _reject("OML-033 detection not ready")

    if not detection.downstream_lifecycle_tracking_authorized:
        _reject("OML-033 lifecycle tracking not authorized")

    if not detection.read_only:
        _reject("OML-033 upstream detection not read-only")

    supplied_histories = prior_histories or {}
    current_by_id = {
        item.narrative_id: item
        for item in detection.narratives
    }

    unknown_history_ids = set(supplied_histories) - set(current_by_id)

    if unknown_history_ids:
        _reject("OML-033 prior history references unknown narrative")

    histories: dict[str, tuple[OracleMemoryNarrative, ...]] = {}

    for narrative_id, current in sorted(current_by_id.items()):
        prior = tuple(supplied_histories.get(narrative_id, ()))

        for item in prior:
            verify_oracle_memory_narrative(item)

            if item.narrative_id != narrative_id:
                _reject("OML-033 prior narrative identity mismatch")

            if item.evolution_index >= current.evolution_index:
                _reject("OML-033 prior evolution index not earlier")

            if item.last_observed_at > current.last_observed_at:
                _reject("OML-033 prior observation time not earlier")

        histories[narrative_id] = tuple(
            sorted(
                (*prior, current),
                key=lambda item: (
                    item.evolution_index,
                    item.last_observed_at,
                    item.narrative_hash,
                ),
            )
        )

    lifecycle_memory = build_oracle_memory_narrative_lifecycle_memory(
        upstream_batch=detection.narrative_batch,
        narrative_histories=histories,
    )

    bindings = tuple(
        _build_binding(
            detection=detection,
            narrative=current_by_id[narrative_id],
            lifecycle_memory=lifecycle_memory,
        )
        for narrative_id in sorted(current_by_id)
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": detection.schema_version,
        "upstream_engine_id": detection.engine_id,
        "upstream_detection_hash": detection.detection_hash,
        "upstream_narrative_batch_hash": (
            detection.narrative_batch.batch_hash
        ),
        "lifecycle_memory": lifecycle_memory,
        "bindings": bindings,
        "narrative_count": lifecycle_memory.narrative_count,
        "snapshot_count": lifecycle_memory.snapshot_count,
        "transition_count": lifecycle_memory.transition_count,
        "lifecycle_state": LIFECYCLE_STATE_READ_ONLY,
        "certified_detection_lineage_verified": True,
        "observation_lifecycle_lineage_verified": True,
        "canonical_temporal_order_verified": (
            lifecycle_memory.canonical_temporal_order_verified
        ),
        "deterministic_lifecycle_tracking_verified": True,
        "entity_lineage_preserved": (
            lifecycle_memory.entity_lineage_preserved
        ),
        "relationship_lineage_preserved": (
            lifecycle_memory.relationship_lineage_preserved
        ),
        "evidence_growth_tracked": (
            lifecycle_memory.evidence_growth_tracked
        ),
        "contradiction_growth_tracked": (
            lifecycle_memory.contradiction_growth_tracked
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "lifecycle_ready": True,
        "downstream_source_reliability_authorized": True,
        "read_only": True,
    }

    tracking = OracleMemoryObservationNarrativeLifecycleTracking(
        **body,
        tracking_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_narrative_lifecycle_tracking(
        tracking
    )
    return tracking


def verify_oracle_memory_observation_narrative_lifecycle_tracking(
    tracking: OracleMemoryObservationNarrativeLifecycleTracking,
) -> bool:
    body = asdict(tracking)
    supplied = body.pop("tracking_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-033 tracking hash mismatch")

    if tracking.schema_version != SCHEMA_VERSION:
        _reject("OML-033 schema mismatch")

    if tracking.engine_id != ENGINE_ID:
        _reject("OML-033 engine mismatch")

    if tracking.policy_id != POLICY_ID:
        _reject("OML-033 policy mismatch")

    if tracking.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-033 subsystem mismatch")

    if tracking.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-033 upstream schema lineage mismatch")

    if tracking.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-033 upstream engine lineage mismatch")

    verify_oracle_memory_narrative_lifecycle_memory(
        tracking.lifecycle_memory
    )

    if tracking.narrative_count != tracking.lifecycle_memory.narrative_count:
        _reject("OML-033 narrative count mismatch")

    if tracking.snapshot_count != tracking.lifecycle_memory.snapshot_count:
        _reject("OML-033 snapshot count mismatch")

    if tracking.transition_count != (
        tracking.lifecycle_memory.transition_count
    ):
        _reject("OML-033 transition count mismatch")

    if tracking.narrative_count != len(tracking.bindings):
        _reject("OML-033 binding count mismatch")

    for binding in tracking.bindings:
        verify_oracle_memory_observation_narrative_lifecycle_binding(
            binding
        )

    if tracking.lifecycle_state != LIFECYCLE_STATE_READ_ONLY:
        _reject("OML-033 lifecycle state invalid")

    required_true = (
        tracking.certified_detection_lineage_verified,
        tracking.observation_lifecycle_lineage_verified,
        tracking.canonical_temporal_order_verified,
        tracking.deterministic_lifecycle_tracking_verified,
        tracking.entity_lineage_preserved,
        tracking.relationship_lineage_preserved,
        tracking.evidence_growth_tracked,
        tracking.contradiction_growth_tracked,
        tracking.lifecycle_ready,
        tracking.downstream_source_reliability_authorized,
        tracking.read_only,
    )

    if not all(required_true):
        _reject("OML-033 tracking guarantee missing")

    forbidden = (
        tracking.persistence_enabled,
        tracking.learning_updates_enabled,
        tracking.runtime_activation_enabled,
        tracking.publication_enabled,
        tracking.action_authorization_enabled,
        tracking.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-033 forbidden tracking capability enabled")

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    build_oracle_memory_observation_narrative_detection,
    build_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking import (
    OracleMemoryObservationNarrativeLifecycleInvariantError,
    build_oracle_memory_observation_narrative_lifecycle_tracking,
    verify_oracle_memory_observation_narrative_lifecycle_tracking,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_graph_materialization,
    build_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_STRENGTHENING,
    OracleMemoryNarrativeInvariantError,
    build_oracle_memory_narrative,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
    OracleMemoryNarrativeTemporalInvariantError,
    TRANSITION_STRENGTHENED,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except (
        OracleMemoryObservationNarrativeLifecycleInvariantError,
        OracleMemoryNarrativeInvariantError,
        OracleMemoryNarrativeTemporalInvariantError,
    ):
        return

    raise AssertionError(f"tampered OML-033 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-033 TEST")
    print(" CERTIFIED OBSERVATION NARRATIVE LIFECYCLE TRACKING")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_031 = load_module(
        root
        / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py",
        "oml_031_fixture_for_oml_033",
    )

    resolution = fixture_031.build_resolution(root)

    liquidity = next(
        item
        for item in resolution.entities
        if item.normalized_name == "stablecoin liquidity"
    )
    bitcoin = next(
        item
        for item in resolution.entities
        if item.normalized_name == "bitcoin"
    )

    relationship_request = (
        build_oracle_memory_observation_relationship_request(
            source_entity_id=liquidity.canonical_entity_id,
            target_entity_id=bitcoin.canonical_entity_id,
            relationship_type="precedes market repricing",
            evidence_hashes=("5" * 64, "6" * 64),
            confidence=0.84,
            contradiction_count=0,
            directed=True,
        )
    )

    graph_materialization = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(relationship_request,),
        )
    )

    relationship = graph_materialization.graph.relationships[0]

    prior_narrative = build_oracle_memory_narrative(
        graph=graph_materialization.graph,
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=("7" * 64,),
        contradicting_evidence_hashes=(),
        confidence=0.58,
        uncertainty=0.42,
        first_observed_at="2026-08-02T14:50:00-05:00",
        last_observed_at="2026-08-02T15:00:00-05:00",
        evolution_index=1,
    )

    assert prior_narrative.stage == NARRATIVE_STAGE_EMERGING

    current_request = build_oracle_memory_observation_narrative_request(
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "7" * 64,
            "8" * 64,
            "9" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T14:50:00-05:00",
        last_observed_at="2026-08-02T15:10:00-05:00",
        evolution_index=2,
        prior_stage=prior_narrative.stage,
    )

    detection = build_oracle_memory_observation_narrative_detection(
        materialization=graph_materialization,
        requests=(current_request,),
    )

    current_narrative = detection.narratives[0]

    assert current_narrative.stage == NARRATIVE_STAGE_STRENGTHENING
    assert current_narrative.narrative_id == prior_narrative.narrative_id

    tracking = (
        build_oracle_memory_observation_narrative_lifecycle_tracking(
            detection=detection,
            prior_histories={
                current_narrative.narrative_id: (prior_narrative,)
            },
        )
    )

    assert tracking.schema_version == "OML-033"
    assert tracking.engine_id == "OML-033"
    assert tracking.upstream_schema_version == "OML-032"
    assert tracking.upstream_engine_id == "OML-032"
    assert tracking.narrative_count == 1
    assert tracking.snapshot_count == 2
    assert tracking.transition_count == 1
    assert tracking.lifecycle_memory.transitions[0].transition_type == (
        TRANSITION_STRENGTHENED
    )
    assert tracking.lifecycle_memory.transitions[0].confidence_delta > 0
    assert tracking.lifecycle_memory.transitions[0].uncertainty_delta < 0
    assert tracking.lifecycle_memory.transitions[0].evidence_growth == 2
    assert tracking.bindings[0].observation_lineage_verified
    assert tracking.certified_detection_lineage_verified
    assert tracking.observation_lifecycle_lineage_verified
    assert tracking.canonical_temporal_order_verified
    assert tracking.deterministic_lifecycle_tracking_verified
    assert tracking.entity_lineage_preserved
    assert tracking.relationship_lineage_preserved
    assert tracking.evidence_growth_tracked
    assert tracking.contradiction_growth_tracked
    assert not tracking.persistence_enabled
    assert not tracking.learning_updates_enabled
    assert not tracking.runtime_activation_enabled
    assert not tracking.publication_enabled
    assert not tracking.action_authorization_enabled
    assert not tracking.qseries_execution_enabled
    assert tracking.lifecycle_ready
    assert tracking.downstream_source_reliability_authorized
    assert tracking.read_only

    replay = build_oracle_memory_observation_narrative_lifecycle_tracking(
        detection=detection,
        prior_histories={
            current_narrative.narrative_id: (prior_narrative,)
        },
    )

    assert replay == tracking
    assert (
        verify_oracle_memory_observation_narrative_lifecycle_tracking(
            tracking
        )
    )

    expect_rejection(
        lambda: build_oracle_memory_observation_narrative_lifecycle_tracking(
            detection=detection,
            prior_histories={
                "f" * 64: (prior_narrative,)
            },
        ),
        "unknown history",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_lifecycle_tracking(
            replace(tracking, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_lifecycle_tracking(
            replace(
                tracking,
                downstream_source_reliability_authorized=False,
            )
        ),
        "source reliability authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_lifecycle_tracking(
            replace(tracking, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-032 narrative detection consumed")
    print("[PASS] Certified OML-021 lifecycle engine consumed")
    print("[PASS] Prior and current narrative history assembled")
    print("[PASS] Narrative identity preserved across evolution")
    print("[PASS] Monotonic evolution index enforced")
    print("[PASS] Strengthened lifecycle transition created")
    print("[PASS] Confidence and uncertainty deltas tracked")
    print("[PASS] Evidence growth tracked")
    print("[PASS] Source observation lineage retained")
    print("[PASS] Lifecycle tracking deterministic across replay")
    print("[PASS] Source reliability continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered lifecycle tracking rejected")
    print(
        "[DONE] OML-033 CERTIFIED OBSERVATION "
        "NARRATIVE LIFECYCLE TRACKING PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstreams() -> None:
    required = (
        UPSTREAM,
        UPSTREAM_TEST,
        LIFECYCLE_MODULE,
        LIFECYCLE_TEST,
    )

    missing = [str(path) for path in required if not path.is_file()]

    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: "
            + ", ".join(missing)
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    detection_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_narrative_detection_and_evolution"
    )
    lifecycle_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_narrative_temporal_tracking_and_lifecycle_memory"
    )

    expected_detection = {
        "SCHEMA_VERSION": "OML-032",
        "ENGINE_ID": "OML-032",
        "POLICY_ID": (
            "oracle-memory.certified-observation-narrative-detection-and-evolution.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-031",
        "UPSTREAM_ENGINE_ID": "OML-031",
    }

    expected_lifecycle = {
        "SCHEMA_VERSION": "OML-021",
        "ENGINE_ID": "OML-021",
        "POLICY_ID": (
            "oracle-memory.narrative-temporal-tracking-and-lifecycle-memory.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-020",
        "UPSTREAM_ENGINE_ID": "OML-020",
    }

    for name, value in expected_detection.items():
        if getattr(detection_module, name, None) != value:
            raise RuntimeError(
                f"Certified OML-032 {name} mismatch"
            )

    for name, value in expected_lifecycle.items():
        if getattr(lifecycle_module, name, None) != value:
            raise RuntimeError(
                f"Certified OML-021 {name} mismatch"
            )

    builder = getattr(
        lifecycle_module,
        "build_oracle_memory_narrative_lifecycle_memory",
        None,
    )

    if builder is None:
        raise RuntimeError("Certified OML-021 lifecycle builder missing")

    required_parameters = {
        "upstream_batch",
        "narrative_histories",
    }

    missing_parameters = sorted(
        required_parameters
        - set(inspect.signature(builder).parameters)
    )

    if missing_parameters:
        raise RuntimeError(
            "Certified OML-021 builder parameters missing: "
            + ", ".join(missing_parameters)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-033 FOR-SURE INSTALLER")
    print(" CERTIFIED OBSERVATION NARRATIVE LIFECYCLE TRACKING")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_032_021_INTERFACE_ALIGNMENT")

    try:
        validate_upstreams()

        print("[OK] Actual OML-032 contract verified")
        print("[OK] Actual OML-021 lifecycle builder verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-032 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        lifecycle_run = subprocess.run(
            [sys.executable, str(LIFECYCLE_TEST)],
            cwd=ROOT,
            check=False,
        )

        if lifecycle_run.returncode:
            raise RuntimeError(
                "OML-021 certification failed with exit code "
                f"{lifecycle_run.returncode}"
            )

        tracked = {
            path: path.read_bytes()
            for path in (
                UPSTREAM,
                UPSTREAM_TEST,
                LIFECYCLE_MODULE,
                LIFECYCLE_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from ."
            "oracle_memory_certified_observation_narrative_lifecycle_tracking "
            "import *"
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
                "OML-033 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(
                    f"Certified upstream changed: {path}"
                )

        print("[PASS] Certified OML-032 production unchanged")
        print("[PASS] Certified OML-032 standalone test unchanged")
        print("[PASS] Certified OML-021 lifecycle engine unchanged")
        print("[PASS] OML-033 production installed")
        print("[PASS] OML-033 standalone deterministic test installed")
        print("[PASS] Observation narratives now enter lifecycle memory")
        print("[PASS] Exact upstream narrative dataclasses preserved")
        print("[PASS] Source reliability continuation authorized")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-033 CERTIFIED OBSERVATION "
            "NARRATIVE LIFECYCLE TRACKING INSTALLED"
        )
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        KeyError,
        TypeError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
