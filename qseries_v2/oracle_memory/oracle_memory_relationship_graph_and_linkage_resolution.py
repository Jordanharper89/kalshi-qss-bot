from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionBatch,
    OracleMemoryResolvedEntity,
    verify_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_resolved_entity,
)

SCHEMA_VERSION = "OML-019"
ENGINE_ID = "OML-019"
POLICY_ID = "oracle-memory.relationship-graph-and-linkage-resolution.v1"

UPSTREAM_SCHEMA_VERSION = "OML-018"
UPSTREAM_ENGINE_ID = "OML-018"

RELATIONSHIP_STATUS_RESOLVED = "resolved"
RELATIONSHIP_STATUS_REJECTED = "rejected"


class OracleMemoryRelationshipGraphInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryEntityRelationship:
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    normalized_relationship_type: str
    evidence_hashes: tuple[str, ...]
    confidence: float
    contradiction_count: int
    directed: bool
    relationship_status: str
    source_entity_verified: bool
    target_entity_verified: bool
    self_link_rejected: bool
    evidence_lineage_verified: bool
    deterministic_identity_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    relationship_hash: str


@dataclass(frozen=True)
class OracleMemoryRelationshipGraph:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    entities: tuple[OracleMemoryResolvedEntity, ...]
    relationships: tuple[OracleMemoryEntityRelationship, ...]
    entity_count: int
    relationship_count: int
    canonical_entity_order_verified: bool
    canonical_relationship_order_verified: bool
    entity_identity_uniqueness_verified: bool
    relationship_identity_uniqueness_verified: bool
    self_links_rejected: bool
    dangling_links_rejected: bool
    duplicate_links_rejected: bool
    deterministic_graph_hashing_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    graph_ready: bool
    next_certification_authorized: bool
    read_only: bool
    graph_hash: str


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

    raise OracleMemoryRelationshipGraphInvariantError(
        "unsupported OML-019 value type: "
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
    raise OracleMemoryRelationshipGraphInvariantError(reason)


def _normalize_relationship_type(value: str) -> str:
    normalized = "_".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-019 relationship type cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-019 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryRelationshipGraphInvariantError(
            f"OML-019 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_entity_relationship(
    *,
    source_entity: OracleMemoryResolvedEntity,
    target_entity: OracleMemoryResolvedEntity,
    relationship_type: str,
    evidence_hashes: Sequence[str],
    confidence: float,
    contradiction_count: int = 0,
    directed: bool = True,
) -> OracleMemoryEntityRelationship:
    verify_oracle_memory_resolved_entity(source_entity)
    verify_oracle_memory_resolved_entity(target_entity)

    if source_entity.canonical_entity_id == target_entity.canonical_entity_id:
        _reject("OML-019 self-links are forbidden")

    normalized_type = _normalize_relationship_type(relationship_type)

    evidence = tuple(evidence_hashes)

    if not evidence:
        _reject("OML-019 relationship evidence is required")

    if len(set(evidence)) != len(evidence):
        _reject("OML-019 duplicate evidence hashes forbidden")

    for value in evidence:
        _require_hash(value, "evidence hash")

    confidence = float(confidence)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-019 confidence outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-019 contradiction count invalid")

    identity_payload = {
        "source_entity_id": source_entity.canonical_entity_id,
        "target_entity_id": target_entity.canonical_entity_id,
        "relationship_type": normalized_type,
        "directed": bool(directed),
    }

    relationship_id = _stable_hash(identity_payload)

    body = {
        "relationship_id": relationship_id,
        "source_entity_id": source_entity.canonical_entity_id,
        "target_entity_id": target_entity.canonical_entity_id,
        "relationship_type": relationship_type.strip(),
        "normalized_relationship_type": normalized_type,
        "evidence_hashes": evidence,
        "confidence": confidence,
        "contradiction_count": contradiction_count,
        "directed": bool(directed),
        "relationship_status": RELATIONSHIP_STATUS_RESOLVED,
        "source_entity_verified": True,
        "target_entity_verified": True,
        "self_link_rejected": True,
        "evidence_lineage_verified": True,
        "deterministic_identity_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    relationship = OracleMemoryEntityRelationship(
        **body,
        relationship_hash=_stable_hash(body),
    )

    verify_oracle_memory_entity_relationship(relationship)
    return relationship


def verify_oracle_memory_entity_relationship(
    relationship: OracleMemoryEntityRelationship,
) -> bool:
    body = asdict(relationship)
    supplied = body.pop("relationship_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-019 relationship hash mismatch")

    _require_hash(relationship.relationship_id, "relationship id")
    _require_hash(
        relationship.source_entity_id,
        "source entity id",
    )
    _require_hash(
        relationship.target_entity_id,
        "target entity id",
    )
    _require_hash(relationship.relationship_hash, "relationship hash")

    if relationship.source_entity_id == relationship.target_entity_id:
        _reject("OML-019 self-link detected")

    if relationship.normalized_relationship_type != (
        _normalize_relationship_type(relationship.relationship_type)
    ):
        _reject("OML-019 relationship type normalization mismatch")

    if not relationship.evidence_hashes:
        _reject("OML-019 relationship evidence missing")

    if len(set(relationship.evidence_hashes)) != len(
        relationship.evidence_hashes
    ):
        _reject("OML-019 duplicate evidence lineage")

    for value in relationship.evidence_hashes:
        _require_hash(value, "relationship evidence hash")

    if not 0.0 <= relationship.confidence <= 1.0:
        _reject("OML-019 relationship confidence invalid")

    if relationship.contradiction_count < 0:
        _reject("OML-019 relationship contradiction count invalid")

    expected_id = _stable_hash(
        {
            "source_entity_id": relationship.source_entity_id,
            "target_entity_id": relationship.target_entity_id,
            "relationship_type": (
                relationship.normalized_relationship_type
            ),
            "directed": relationship.directed,
        }
    )

    if relationship.relationship_id != expected_id:
        _reject("OML-019 relationship identity mismatch")

    required_true = (
        relationship.source_entity_verified,
        relationship.target_entity_verified,
        relationship.self_link_rejected,
        relationship.evidence_lineage_verified,
        relationship.deterministic_identity_verified,
        relationship.read_only,
    )

    if not all(required_true):
        _reject("OML-019 relationship guarantee missing")

    forbidden = (
        relationship.persistence_authorized,
        relationship.learning_update_authorized,
        relationship.runtime_activation_authorized,
        relationship.publication_authorized,
        relationship.action_authorization_enabled,
        relationship.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-019 forbidden relationship capability enabled")

    return True


def build_oracle_memory_relationship_graph(
    *,
    entity_batch: OracleMemoryEntityResolutionBatch,
    relationships: Sequence[OracleMemoryEntityRelationship],
) -> OracleMemoryRelationshipGraph:
    verify_oracle_memory_entity_resolution_batch(entity_batch)

    if entity_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-019 upstream schema mismatch")

    if entity_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-019 upstream engine mismatch")

    if not entity_batch.batch_ready:
        _reject("OML-019 upstream entity batch not ready")

    if not entity_batch.next_certification_authorized:
        _reject("OML-019 upstream continuation not authorized")

    if not entity_batch.read_only:
        _reject("OML-019 upstream read-only guarantee missing")

    entities = tuple(
        sorted(
            entity_batch.entities,
            key=lambda item: (
                item.domain_id,
                item.normalized_name,
                item.canonical_entity_id,
            ),
        )
    )

    entity_ids = {
        entity.canonical_entity_id
        for entity in entities
    }

    ordered_relationships = tuple(
        sorted(
            relationships,
            key=lambda item: (
                item.source_entity_id,
                item.target_entity_id,
                item.normalized_relationship_type,
                item.relationship_id,
            ),
        )
    )

    for relationship in ordered_relationships:
        verify_oracle_memory_entity_relationship(relationship)

        if relationship.source_entity_id not in entity_ids:
            _reject("OML-019 dangling source entity")

        if relationship.target_entity_id not in entity_ids:
            _reject("OML-019 dangling target entity")

    relationship_ids = tuple(
        relationship.relationship_id
        for relationship in ordered_relationships
    )

    if len(set(relationship_ids)) != len(relationship_ids):
        _reject("OML-019 duplicate relationships forbidden")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": entity_batch.schema_version,
        "upstream_engine_id": entity_batch.engine_id,
        "upstream_batch_hash": entity_batch.batch_hash,
        "entities": entities,
        "relationships": ordered_relationships,
        "entity_count": len(entities),
        "relationship_count": len(ordered_relationships),
        "canonical_entity_order_verified": True,
        "canonical_relationship_order_verified": True,
        "entity_identity_uniqueness_verified": (
            len(entity_ids) == len(entities)
        ),
        "relationship_identity_uniqueness_verified": (
            len(set(relationship_ids)) == len(relationship_ids)
        ),
        "self_links_rejected": all(
            item.source_entity_id != item.target_entity_id
            for item in ordered_relationships
        ),
        "dangling_links_rejected": True,
        "duplicate_links_rejected": True,
        "deterministic_graph_hashing_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "graph_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    graph = OracleMemoryRelationshipGraph(
        **body,
        graph_hash=_stable_hash(body),
    )

    verify_oracle_memory_relationship_graph(graph)
    return graph


def verify_oracle_memory_relationship_graph(
    graph: OracleMemoryRelationshipGraph,
) -> bool:
    body = asdict(graph)
    supplied = body.pop("graph_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-019 graph hash mismatch")

    if graph.schema_version != SCHEMA_VERSION:
        _reject("OML-019 graph schema mismatch")

    if graph.engine_id != ENGINE_ID:
        _reject("OML-019 graph engine mismatch")

    if graph.policy_id != POLICY_ID:
        _reject("OML-019 graph policy mismatch")

    if graph.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-019 graph subsystem mismatch")

    if graph.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-019 upstream schema lineage mismatch")

    if graph.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-019 upstream engine lineage mismatch")

    if graph.entity_count != len(graph.entities):
        _reject("OML-019 entity count mismatch")

    if graph.relationship_count != len(graph.relationships):
        _reject("OML-019 relationship count mismatch")

    entity_ids = {
        entity.canonical_entity_id
        for entity in graph.entities
    }

    if len(entity_ids) != len(graph.entities):
        _reject("OML-019 duplicate entity identities")

    relationship_ids = []

    for entity in graph.entities:
        verify_oracle_memory_resolved_entity(entity)

    for relationship in graph.relationships:
        verify_oracle_memory_entity_relationship(relationship)

        if relationship.source_entity_id not in entity_ids:
            _reject("OML-019 graph contains dangling source")

        if relationship.target_entity_id not in entity_ids:
            _reject("OML-019 graph contains dangling target")

        relationship_ids.append(relationship.relationship_id)

    if len(set(relationship_ids)) != len(relationship_ids):
        _reject("OML-019 graph contains duplicate links")

    required_true = (
        graph.canonical_entity_order_verified,
        graph.canonical_relationship_order_verified,
        graph.entity_identity_uniqueness_verified,
        graph.relationship_identity_uniqueness_verified,
        graph.self_links_rejected,
        graph.dangling_links_rejected,
        graph.duplicate_links_rejected,
        graph.deterministic_graph_hashing_verified,
        graph.graph_ready,
        graph.next_certification_authorized,
        graph.read_only,
    )

    if not all(required_true):
        _reject("OML-019 graph guarantee missing")

    forbidden = (
        graph.persistence_enabled,
        graph.learning_updates_enabled,
        graph.runtime_activation_enabled,
        graph.publication_enabled,
        graph.action_authorization_enabled,
        graph.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-019 forbidden graph capability enabled")

    return True
