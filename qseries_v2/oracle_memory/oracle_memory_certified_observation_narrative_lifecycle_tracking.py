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
