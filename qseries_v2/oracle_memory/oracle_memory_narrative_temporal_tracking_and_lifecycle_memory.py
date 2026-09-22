from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    ALLOWED_STAGES,
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_RESOLVED,
    NARRATIVE_STAGE_STRENGTHENING,
    NARRATIVE_STAGE_WEAKENING,
    OracleMemoryNarrative,
    OracleMemoryNarrativeEvolutionBatch,
    verify_oracle_memory_narrative,
    verify_oracle_memory_narrative_evolution_batch,
)

SCHEMA_VERSION = "OML-021"
ENGINE_ID = "OML-021"
POLICY_ID = (
    "oracle-memory.narrative-temporal-tracking-and-lifecycle-memory.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-020"
UPSTREAM_ENGINE_ID = "OML-020"

TRANSITION_STABLE = "stable"
TRANSITION_STRENGTHENED = "strengthened"
TRANSITION_WEAKENED = "weakened"
TRANSITION_RESOLVED = "resolved"
TRANSITION_REOPENED = "reopened"

ALLOWED_TRANSITIONS = (
    TRANSITION_STABLE,
    TRANSITION_STRENGTHENED,
    TRANSITION_WEAKENED,
    TRANSITION_RESOLVED,
    TRANSITION_REOPENED,
)

_STAGE_RANK = {
    NARRATIVE_STAGE_WEAKENING: 0,
    NARRATIVE_STAGE_EMERGING: 1,
    NARRATIVE_STAGE_STRENGTHENING: 2,
    NARRATIVE_STAGE_RESOLVED: 3,
}


class OracleMemoryNarrativeTemporalInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryNarrativeTemporalSnapshot:
    narrative_id: str
    narrative_hash: str
    stage: str
    confidence: float
    uncertainty: float
    contradiction_count: int
    observed_at: str
    evolution_index: int
    participating_entity_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    supporting_evidence_hashes: tuple[str, ...]
    contradicting_evidence_hashes: tuple[str, ...]
    snapshot_hash: str


@dataclass(frozen=True)
class OracleMemoryNarrativeLifecycleTransition:
    narrative_id: str
    prior_snapshot_hash: str
    current_snapshot_hash: str
    prior_stage: str
    current_stage: str
    transition_type: str
    confidence_delta: float
    uncertainty_delta: float
    contradiction_delta: int
    evidence_growth: int
    entity_lineage_stable: bool
    relationship_lineage_stable: bool
    temporal_order_verified: bool
    lifecycle_rules_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    transition_hash: str


@dataclass(frozen=True)
class OracleMemoryNarrativeLifecycleMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    snapshots: tuple[OracleMemoryNarrativeTemporalSnapshot, ...]
    transitions: tuple[OracleMemoryNarrativeLifecycleTransition, ...]
    narrative_count: int
    snapshot_count: int
    transition_count: int
    canonical_temporal_order_verified: bool
    deterministic_snapshot_hashing_verified: bool
    deterministic_transition_hashing_verified: bool
    stage_transition_rules_verified: bool
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
    memory_ready: bool
    next_certification_authorized: bool
    read_only: bool
    memory_hash: str


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

    raise OracleMemoryNarrativeTemporalInvariantError(
        "unsupported OML-021 value type: "
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
    raise OracleMemoryNarrativeTemporalInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-021 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryNarrativeTemporalInvariantError(
            f"OML-021 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_narrative_temporal_snapshot(
    narrative: OracleMemoryNarrative,
) -> OracleMemoryNarrativeTemporalSnapshot:
    verify_oracle_memory_narrative(narrative)

    body = {
        "narrative_id": narrative.narrative_id,
        "narrative_hash": narrative.narrative_hash,
        "stage": narrative.stage,
        "confidence": narrative.confidence,
        "uncertainty": narrative.uncertainty,
        "contradiction_count": narrative.contradiction_count,
        "observed_at": narrative.last_observed_at,
        "evolution_index": narrative.evolution_index,
        "participating_entity_ids": narrative.participating_entity_ids,
        "relationship_ids": narrative.relationship_ids,
        "supporting_evidence_hashes": (
            narrative.supporting_evidence_hashes
        ),
        "contradicting_evidence_hashes": (
            narrative.contradicting_evidence_hashes
        ),
    }

    snapshot = OracleMemoryNarrativeTemporalSnapshot(
        **body,
        snapshot_hash=_stable_hash(body),
    )

    verify_oracle_memory_narrative_temporal_snapshot(snapshot)
    return snapshot


def verify_oracle_memory_narrative_temporal_snapshot(
    snapshot: OracleMemoryNarrativeTemporalSnapshot,
) -> bool:
    body = asdict(snapshot)
    supplied = body.pop("snapshot_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-021 snapshot hash mismatch")

    for value, label in (
        (snapshot.narrative_id, "narrative id"),
        (snapshot.narrative_hash, "narrative hash"),
        (snapshot.snapshot_hash, "snapshot hash"),
    ):
        _require_hash(value, label)

    if snapshot.stage not in ALLOWED_STAGES:
        _reject("OML-021 snapshot stage invalid")

    if not 0.0 <= snapshot.confidence <= 1.0:
        _reject("OML-021 snapshot confidence invalid")

    if not 0.0 <= snapshot.uncertainty <= 1.0:
        _reject("OML-021 snapshot uncertainty invalid")

    if snapshot.contradiction_count < 0:
        _reject("OML-021 snapshot contradiction count invalid")

    if not snapshot.observed_at.strip():
        _reject("OML-021 snapshot observed_at missing")

    if snapshot.evolution_index < 1:
        _reject("OML-021 snapshot evolution index invalid")

    if not snapshot.participating_entity_ids:
        _reject("OML-021 snapshot entity lineage missing")

    return True


def _derive_transition(
    prior: OracleMemoryNarrativeTemporalSnapshot,
    current: OracleMemoryNarrativeTemporalSnapshot,
) -> str:
    if prior.stage == NARRATIVE_STAGE_RESOLVED:
        if current.stage == NARRATIVE_STAGE_RESOLVED:
            return TRANSITION_STABLE
        return TRANSITION_REOPENED

    if current.stage == NARRATIVE_STAGE_RESOLVED:
        return TRANSITION_RESOLVED

    prior_rank = _STAGE_RANK[prior.stage]
    current_rank = _STAGE_RANK[current.stage]

    if current_rank > prior_rank:
        return TRANSITION_STRENGTHENED

    if current_rank < prior_rank:
        return TRANSITION_WEAKENED

    return TRANSITION_STABLE


def build_oracle_memory_narrative_lifecycle_transition(
    *,
    prior: OracleMemoryNarrativeTemporalSnapshot,
    current: OracleMemoryNarrativeTemporalSnapshot,
) -> OracleMemoryNarrativeLifecycleTransition:
    verify_oracle_memory_narrative_temporal_snapshot(prior)
    verify_oracle_memory_narrative_temporal_snapshot(current)

    if prior.narrative_id != current.narrative_id:
        _reject("OML-021 transition narrative identity mismatch")

    if current.evolution_index <= prior.evolution_index:
        _reject("OML-021 non-monotonic evolution index")

    if current.observed_at < prior.observed_at:
        _reject("OML-021 non-monotonic observation time")

    transition_type = _derive_transition(prior, current)

    body = {
        "narrative_id": current.narrative_id,
        "prior_snapshot_hash": prior.snapshot_hash,
        "current_snapshot_hash": current.snapshot_hash,
        "prior_stage": prior.stage,
        "current_stage": current.stage,
        "transition_type": transition_type,
        "confidence_delta": round(
            current.confidence - prior.confidence,
            12,
        ),
        "uncertainty_delta": round(
            current.uncertainty - prior.uncertainty,
            12,
        ),
        "contradiction_delta": (
            current.contradiction_count - prior.contradiction_count
        ),
        "evidence_growth": (
            len(current.supporting_evidence_hashes)
            - len(prior.supporting_evidence_hashes)
        ),
        "entity_lineage_stable": (
            current.participating_entity_ids
            == prior.participating_entity_ids
        ),
        "relationship_lineage_stable": (
            current.relationship_ids == prior.relationship_ids
        ),
        "temporal_order_verified": True,
        "lifecycle_rules_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    transition = OracleMemoryNarrativeLifecycleTransition(
        **body,
        transition_hash=_stable_hash(body),
    )

    verify_oracle_memory_narrative_lifecycle_transition(transition)
    return transition


def verify_oracle_memory_narrative_lifecycle_transition(
    transition: OracleMemoryNarrativeLifecycleTransition,
) -> bool:
    body = asdict(transition)
    supplied = body.pop("transition_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-021 transition hash mismatch")

    for value, label in (
        (transition.narrative_id, "narrative id"),
        (transition.prior_snapshot_hash, "prior snapshot hash"),
        (transition.current_snapshot_hash, "current snapshot hash"),
        (transition.transition_hash, "transition hash"),
    ):
        _require_hash(value, label)

    if transition.prior_stage not in ALLOWED_STAGES:
        _reject("OML-021 prior stage invalid")

    if transition.current_stage not in ALLOWED_STAGES:
        _reject("OML-021 current stage invalid")

    if transition.transition_type not in ALLOWED_TRANSITIONS:
        _reject("OML-021 transition type invalid")

    required_true = (
        transition.entity_lineage_stable,
        transition.relationship_lineage_stable,
        transition.temporal_order_verified,
        transition.lifecycle_rules_verified,
        transition.read_only,
    )

    if not all(required_true):
        _reject("OML-021 transition guarantee missing")

    forbidden = (
        transition.persistence_authorized,
        transition.learning_update_authorized,
        transition.runtime_activation_authorized,
        transition.publication_authorized,
        transition.action_authorization_enabled,
        transition.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-021 forbidden transition capability enabled")

    return True


def build_oracle_memory_narrative_lifecycle_memory(
    *,
    upstream_batch: OracleMemoryNarrativeEvolutionBatch,
    narrative_histories: Mapping[str, Sequence[OracleMemoryNarrative]],
) -> OracleMemoryNarrativeLifecycleMemory:
    verify_oracle_memory_narrative_evolution_batch(upstream_batch)

    if upstream_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-021 upstream schema mismatch")

    if upstream_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-021 upstream engine mismatch")

    if not upstream_batch.batch_ready:
        _reject("OML-021 upstream batch not ready")

    if not upstream_batch.next_certification_authorized:
        _reject("OML-021 upstream continuation not authorized")

    if not upstream_batch.read_only:
        _reject("OML-021 upstream batch is not read-only")

    snapshots = []
    transitions = []

    for narrative_id in sorted(narrative_histories):
        history = tuple(
            sorted(
                narrative_histories[narrative_id],
                key=lambda item: (
                    item.evolution_index,
                    item.last_observed_at,
                    item.narrative_hash,
                ),
            )
        )

        if not history:
            _reject("OML-021 narrative history cannot be empty")

        if any(item.narrative_id != narrative_id for item in history):
            _reject("OML-021 narrative history identity mismatch")

        narrative_snapshots = tuple(
            build_oracle_memory_narrative_temporal_snapshot(item)
            for item in history
        )

        snapshots.extend(narrative_snapshots)

        for index in range(1, len(narrative_snapshots)):
            transitions.append(
                build_oracle_memory_narrative_lifecycle_transition(
                    prior=narrative_snapshots[index - 1],
                    current=narrative_snapshots[index],
                )
            )

    ordered_snapshots = tuple(
        sorted(
            snapshots,
            key=lambda item: (
                item.narrative_id,
                item.evolution_index,
                item.observed_at,
                item.snapshot_hash,
            ),
        )
    )

    ordered_transitions = tuple(
        sorted(
            transitions,
            key=lambda item: (
                item.narrative_id,
                item.prior_snapshot_hash,
                item.current_snapshot_hash,
            ),
        )
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": upstream_batch.schema_version,
        "upstream_engine_id": upstream_batch.engine_id,
        "upstream_batch_hash": upstream_batch.batch_hash,
        "snapshots": ordered_snapshots,
        "transitions": ordered_transitions,
        "narrative_count": len(narrative_histories),
        "snapshot_count": len(ordered_snapshots),
        "transition_count": len(ordered_transitions),
        "canonical_temporal_order_verified": True,
        "deterministic_snapshot_hashing_verified": True,
        "deterministic_transition_hashing_verified": True,
        "stage_transition_rules_verified": True,
        "entity_lineage_preserved": all(
            item.entity_lineage_stable
            for item in ordered_transitions
        ),
        "relationship_lineage_preserved": all(
            item.relationship_lineage_stable
            for item in ordered_transitions
        ),
        "evidence_growth_tracked": True,
        "contradiction_growth_tracked": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    memory = OracleMemoryNarrativeLifecycleMemory(
        **body,
        memory_hash=_stable_hash(body),
    )

    verify_oracle_memory_narrative_lifecycle_memory(memory)
    return memory


def verify_oracle_memory_narrative_lifecycle_memory(
    memory: OracleMemoryNarrativeLifecycleMemory,
) -> bool:
    body = asdict(memory)
    supplied = body.pop("memory_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-021 memory hash mismatch")

    if memory.schema_version != SCHEMA_VERSION:
        _reject("OML-021 schema mismatch")

    if memory.engine_id != ENGINE_ID:
        _reject("OML-021 engine mismatch")

    if memory.policy_id != POLICY_ID:
        _reject("OML-021 policy mismatch")

    if memory.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-021 subsystem mismatch")

    if memory.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-021 upstream schema lineage mismatch")

    if memory.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-021 upstream engine lineage mismatch")

    if memory.snapshot_count != len(memory.snapshots):
        _reject("OML-021 snapshot count mismatch")

    if memory.transition_count != len(memory.transitions):
        _reject("OML-021 transition count mismatch")

    for snapshot in memory.snapshots:
        verify_oracle_memory_narrative_temporal_snapshot(snapshot)

    for transition in memory.transitions:
        verify_oracle_memory_narrative_lifecycle_transition(transition)

    required_true = (
        memory.canonical_temporal_order_verified,
        memory.deterministic_snapshot_hashing_verified,
        memory.deterministic_transition_hashing_verified,
        memory.stage_transition_rules_verified,
        memory.entity_lineage_preserved,
        memory.relationship_lineage_preserved,
        memory.evidence_growth_tracked,
        memory.contradiction_growth_tracked,
        memory.memory_ready,
        memory.next_certification_authorized,
        memory.read_only,
    )

    if not all(required_true):
        _reject("OML-021 lifecycle guarantee missing")

    forbidden = (
        memory.persistence_enabled,
        memory.learning_updates_enabled,
        memory.runtime_activation_enabled,
        memory.publication_enabled,
        memory.action_authorization_enabled,
        memory.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-021 forbidden lifecycle capability enabled")

    return True
