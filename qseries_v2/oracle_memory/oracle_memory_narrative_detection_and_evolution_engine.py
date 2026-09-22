from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    OracleMemoryEntityRelationship,
    OracleMemoryRelationshipGraph,
    verify_oracle_memory_entity_relationship,
    verify_oracle_memory_relationship_graph,
)

SCHEMA_VERSION = "OML-020"
ENGINE_ID = "OML-020"
POLICY_ID = "oracle-memory.narrative-detection-and-evolution-engine.v1"

UPSTREAM_SCHEMA_VERSION = "OML-019"
UPSTREAM_ENGINE_ID = "OML-019"

NARRATIVE_STAGE_EMERGING = "emerging"
NARRATIVE_STAGE_STRENGTHENING = "strengthening"
NARRATIVE_STAGE_WEAKENING = "weakening"
NARRATIVE_STAGE_RESOLVED = "resolved"

ALLOWED_STAGES = (
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_STRENGTHENING,
    NARRATIVE_STAGE_WEAKENING,
    NARRATIVE_STAGE_RESOLVED,
)


class OracleMemoryNarrativeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryNarrative:
    narrative_id: str
    title: str
    normalized_title: str
    stage: str
    participating_entity_ids: tuple[str, ...]
    relationship_ids: tuple[str, ...]
    supporting_evidence_hashes: tuple[str, ...]
    contradicting_evidence_hashes: tuple[str, ...]
    confidence: float
    uncertainty: float
    contradiction_count: int
    first_observed_at: str
    last_observed_at: str
    evolution_index: int
    entity_lineage_verified: bool
    relationship_lineage_verified: bool
    evidence_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_order_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    narrative_hash: str


@dataclass(frozen=True)
class OracleMemoryNarrativeEvolutionBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_graph_hash: str
    narratives: tuple[OracleMemoryNarrative, ...]
    narrative_count: int
    emerging_count: int
    strengthening_count: int
    weakening_count: int
    resolved_count: int
    canonical_order_verified: bool
    deterministic_detection_verified: bool
    deterministic_evolution_verified: bool
    entity_lineage_verified: bool
    relationship_lineage_verified: bool
    supporting_evidence_verified: bool
    contradiction_tracking_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    batch_ready: bool
    next_certification_authorized: bool
    read_only: bool
    batch_hash: str


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

    raise OracleMemoryNarrativeInvariantError(
        "unsupported OML-020 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryNarrativeInvariantError(reason)


def _normalize_text(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-020 normalized text cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-020 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryNarrativeInvariantError(
            f"OML-020 invalid {label} hexadecimal value"
        ) from exc


def _derive_stage(
    *,
    supporting_evidence_count: int,
    contradiction_count: int,
    confidence: float,
    prior_stage: str | None,
) -> str:
    if prior_stage == NARRATIVE_STAGE_RESOLVED:
        return NARRATIVE_STAGE_RESOLVED

    if contradiction_count > supporting_evidence_count:
        return NARRATIVE_STAGE_WEAKENING

    if supporting_evidence_count >= 3 and confidence >= 0.70:
        return NARRATIVE_STAGE_STRENGTHENING

    return NARRATIVE_STAGE_EMERGING


def build_oracle_memory_narrative(
    *,
    graph: OracleMemoryRelationshipGraph,
    title: str,
    participating_entity_ids: Sequence[str],
    relationship_ids: Sequence[str],
    supporting_evidence_hashes: Sequence[str],
    contradicting_evidence_hashes: Sequence[str] = (),
    confidence: float,
    uncertainty: float,
    first_observed_at: str,
    last_observed_at: str,
    evolution_index: int = 1,
    prior_stage: str | None = None,
) -> OracleMemoryNarrative:
    verify_oracle_memory_relationship_graph(graph)

    if graph.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-020 upstream graph schema mismatch")

    if graph.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-020 upstream graph engine mismatch")

    if not graph.graph_ready:
        _reject("OML-020 upstream graph not ready")

    if not graph.next_certification_authorized:
        _reject("OML-020 upstream continuation not authorized")

    if not graph.read_only:
        _reject("OML-020 upstream graph is not read-only")

    normalized_title = _normalize_text(title)

    entity_ids = tuple(sorted(set(participating_entity_ids)))
    rel_ids = tuple(sorted(set(relationship_ids)))
    supporting = tuple(sorted(set(supporting_evidence_hashes)))
    contradicting = tuple(sorted(set(contradicting_evidence_hashes)))

    if not entity_ids:
        _reject("OML-020 narrative requires participating entities")

    graph_entity_ids = {
        entity.canonical_entity_id
        for entity in graph.entities
    }

    if any(entity_id not in graph_entity_ids for entity_id in entity_ids):
        _reject("OML-020 narrative contains unknown entity")

    graph_relationships = {
        relationship.relationship_id: relationship
        for relationship in graph.relationships
    }

    if any(rel_id not in graph_relationships for rel_id in rel_ids):
        _reject("OML-020 narrative contains unknown relationship")

    for rel_id in rel_ids:
        verify_oracle_memory_entity_relationship(
            graph_relationships[rel_id]
        )

    if not supporting:
        _reject("OML-020 narrative requires supporting evidence")

    for value in (*supporting, *contradicting):
        _require_hash(value, "evidence hash")

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-020 confidence outside [0, 1]")

    if not 0.0 <= uncertainty <= 1.0:
        _reject("OML-020 uncertainty outside [0, 1]")

    if (
        not isinstance(evolution_index, int)
        or isinstance(evolution_index, bool)
        or evolution_index < 1
    ):
        _reject("OML-020 evolution index invalid")

    if not isinstance(first_observed_at, str) or not first_observed_at.strip():
        _reject("OML-020 first_observed_at required")

    if not isinstance(last_observed_at, str) or not last_observed_at.strip():
        _reject("OML-020 last_observed_at required")

    stage = _derive_stage(
        supporting_evidence_count=len(supporting),
        contradiction_count=len(contradicting),
        confidence=confidence,
        prior_stage=prior_stage,
    )

    narrative_id = _stable_hash(
        {
            "normalized_title": normalized_title,
            "participating_entity_ids": entity_ids,
        }
    )

    body = {
        "narrative_id": narrative_id,
        "title": title.strip(),
        "normalized_title": normalized_title,
        "stage": stage,
        "participating_entity_ids": entity_ids,
        "relationship_ids": rel_ids,
        "supporting_evidence_hashes": supporting,
        "contradicting_evidence_hashes": contradicting,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "contradiction_count": len(contradicting),
        "first_observed_at": first_observed_at.strip(),
        "last_observed_at": last_observed_at.strip(),
        "evolution_index": evolution_index,
        "entity_lineage_verified": True,
        "relationship_lineage_verified": True,
        "evidence_lineage_verified": True,
        "deterministic_identity_verified": True,
        "canonical_order_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    narrative = OracleMemoryNarrative(
        **body,
        narrative_hash=_stable_hash(body),
    )

    verify_oracle_memory_narrative(narrative)
    return narrative


def verify_oracle_memory_narrative(
    narrative: OracleMemoryNarrative,
) -> bool:
    body = asdict(narrative)
    supplied = body.pop("narrative_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-020 narrative hash mismatch")

    _require_hash(narrative.narrative_id, "narrative id")
    _require_hash(narrative.narrative_hash, "narrative hash")

    if narrative.normalized_title != _normalize_text(narrative.title):
        _reject("OML-020 title normalization mismatch")

    if narrative.stage not in ALLOWED_STAGES:
        _reject("OML-020 narrative stage invalid")

    if not narrative.participating_entity_ids:
        _reject("OML-020 narrative entity lineage missing")

    if not narrative.supporting_evidence_hashes:
        _reject("OML-020 supporting evidence missing")

    for value in (
        *narrative.participating_entity_ids,
        *narrative.relationship_ids,
        *narrative.supporting_evidence_hashes,
        *narrative.contradicting_evidence_hashes,
    ):
        _require_hash(value, "narrative lineage hash")

    if tuple(sorted(set(narrative.participating_entity_ids))) != (
        narrative.participating_entity_ids
    ):
        _reject("OML-020 entity order or uniqueness invalid")

    if tuple(sorted(set(narrative.relationship_ids))) != (
        narrative.relationship_ids
    ):
        _reject("OML-020 relationship order or uniqueness invalid")

    if tuple(sorted(set(narrative.supporting_evidence_hashes))) != (
        narrative.supporting_evidence_hashes
    ):
        _reject("OML-020 supporting evidence order invalid")

    if tuple(sorted(set(narrative.contradicting_evidence_hashes))) != (
        narrative.contradicting_evidence_hashes
    ):
        _reject("OML-020 contradicting evidence order invalid")

    if not 0.0 <= narrative.confidence <= 1.0:
        _reject("OML-020 narrative confidence invalid")

    if not 0.0 <= narrative.uncertainty <= 1.0:
        _reject("OML-020 narrative uncertainty invalid")

    if narrative.contradiction_count != len(
        narrative.contradicting_evidence_hashes
    ):
        _reject("OML-020 contradiction count mismatch")

    if narrative.evolution_index < 1:
        _reject("OML-020 evolution index invalid")

    expected_id = _stable_hash(
        {
            "normalized_title": narrative.normalized_title,
            "participating_entity_ids": (
                narrative.participating_entity_ids
            ),
        }
    )

    if narrative.narrative_id != expected_id:
        _reject("OML-020 narrative identity mismatch")

    required_true = (
        narrative.entity_lineage_verified,
        narrative.relationship_lineage_verified,
        narrative.evidence_lineage_verified,
        narrative.deterministic_identity_verified,
        narrative.canonical_order_verified,
        narrative.read_only,
    )

    if not all(required_true):
        _reject("OML-020 narrative guarantee missing")

    forbidden = (
        narrative.persistence_authorized,
        narrative.learning_update_authorized,
        narrative.runtime_activation_authorized,
        narrative.publication_authorized,
        narrative.action_authorization_enabled,
        narrative.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-020 forbidden narrative capability enabled")

    return True


def build_oracle_memory_narrative_evolution_batch(
    *,
    graph: OracleMemoryRelationshipGraph,
    narratives: Sequence[OracleMemoryNarrative],
) -> OracleMemoryNarrativeEvolutionBatch:
    verify_oracle_memory_relationship_graph(graph)

    ordered = tuple(
        sorted(
            narratives,
            key=lambda item: (
                item.normalized_title,
                item.narrative_id,
                item.evolution_index,
            ),
        )
    )

    for narrative in ordered:
        verify_oracle_memory_narrative(narrative)

    narrative_ids = tuple(
        narrative.narrative_id
        for narrative in ordered
    )

    if len(set(narrative_ids)) != len(narrative_ids):
        _reject("OML-020 duplicate narrative identities forbidden")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": graph.schema_version,
        "upstream_engine_id": graph.engine_id,
        "upstream_graph_hash": graph.graph_hash,
        "narratives": ordered,
        "narrative_count": len(ordered),
        "emerging_count": sum(
            item.stage == NARRATIVE_STAGE_EMERGING
            for item in ordered
        ),
        "strengthening_count": sum(
            item.stage == NARRATIVE_STAGE_STRENGTHENING
            for item in ordered
        ),
        "weakening_count": sum(
            item.stage == NARRATIVE_STAGE_WEAKENING
            for item in ordered
        ),
        "resolved_count": sum(
            item.stage == NARRATIVE_STAGE_RESOLVED
            for item in ordered
        ),
        "canonical_order_verified": True,
        "deterministic_detection_verified": True,
        "deterministic_evolution_verified": True,
        "entity_lineage_verified": True,
        "relationship_lineage_verified": True,
        "supporting_evidence_verified": True,
        "contradiction_tracking_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "batch_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    batch = OracleMemoryNarrativeEvolutionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_narrative_evolution_batch(batch)
    return batch


def verify_oracle_memory_narrative_evolution_batch(
    batch: OracleMemoryNarrativeEvolutionBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-020 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-020 batch schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-020 batch engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-020 batch policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-020 batch subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-020 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-020 upstream engine lineage mismatch")

    if batch.narrative_count != len(batch.narratives):
        _reject("OML-020 narrative count mismatch")

    if (
        batch.emerging_count
        + batch.strengthening_count
        + batch.weakening_count
        + batch.resolved_count
        != batch.narrative_count
    ):
        _reject("OML-020 stage count reconciliation mismatch")

    narrative_ids = []

    for narrative in batch.narratives:
        verify_oracle_memory_narrative(narrative)
        narrative_ids.append(narrative.narrative_id)

    if len(set(narrative_ids)) != len(narrative_ids):
        _reject("OML-020 duplicate narrative ids")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_detection_verified,
        batch.deterministic_evolution_verified,
        batch.entity_lineage_verified,
        batch.relationship_lineage_verified,
        batch.supporting_evidence_verified,
        batch.contradiction_tracking_verified,
        batch.batch_ready,
        batch.next_certification_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-020 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-020 forbidden batch capability enabled")

    return True
