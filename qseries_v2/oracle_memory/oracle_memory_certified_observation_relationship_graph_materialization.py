from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_entity_resolution import (
    OracleMemoryObservationEntityResolution,
    verify_oracle_memory_observation_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionBatch,
    verify_oracle_memory_entity_resolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    OracleMemoryEntityRelationship,
    OracleMemoryRelationshipGraph,
    build_oracle_memory_entity_relationship,
    build_oracle_memory_relationship_graph,
    verify_oracle_memory_entity_relationship,
    verify_oracle_memory_relationship_graph,
)

SCHEMA_VERSION = "OML-031"
ENGINE_ID = "OML-031"
POLICY_ID = (
    "oracle-memory.certified-observation-relationship-graph-materialization.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-030"
UPSTREAM_ENGINE_ID = "OML-030"

GRAPH_STATE_READ_ONLY = "read_only_graph"


class OracleMemoryObservationRelationshipGraphInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationRelationshipRequest:
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    evidence_hashes: tuple[str, ...]
    confidence: float
    contradiction_count: int
    directed: bool
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationRelationshipBinding:
    request_hash: str
    relationship_id: str
    relationship_hash: str
    source_entity_id: str
    target_entity_id: str
    source_observation_hash: str
    target_observation_hash: str
    source_entity_lineage_verified: bool
    target_entity_lineage_verified: bool
    evidence_lineage_verified: bool
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
class OracleMemoryObservationRelationshipGraphMaterialization:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_resolution_hash: str
    adapted_entity_batch_hash: str
    relationship_graph_hash: str
    graph: OracleMemoryRelationshipGraph
    bindings: tuple[OracleMemoryObservationRelationshipBinding, ...]
    entity_count: int
    relationship_count: int
    graph_state: str
    certified_entity_lineage_verified: bool
    observation_relationship_lineage_verified: bool
    canonical_graph_order_verified: bool
    deterministic_graph_materialization_verified: bool
    dangling_relationships_rejected: bool
    duplicate_relationships_rejected: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    graph_ready: bool
    downstream_narrative_detection_authorized: bool
    read_only: bool
    materialization_hash: str


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
    raise OracleMemoryObservationRelationshipGraphInvariantError(
        "unsupported OML-031 value type: "
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
    raise OracleMemoryObservationRelationshipGraphInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-031 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationRelationshipGraphInvariantError(
            f"OML-031 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_observation_relationship_request(
    *,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    evidence_hashes: Sequence[str],
    confidence: float,
    contradiction_count: int = 0,
    directed: bool = True,
) -> OracleMemoryObservationRelationshipRequest:
    _require_hash(source_entity_id, "source entity id")
    _require_hash(target_entity_id, "target entity id")

    if source_entity_id == target_entity_id:
        _reject("OML-031 self relationship forbidden")

    if not isinstance(relationship_type, str) or not relationship_type.strip():
        _reject("OML-031 relationship type required")

    evidence = tuple(sorted(set(evidence_hashes)))

    if not evidence:
        _reject("OML-031 relationship evidence required")

    if len(evidence) != len(tuple(evidence_hashes)):
        _reject("OML-031 duplicate evidence hashes forbidden")

    for value in evidence:
        _require_hash(value, "evidence hash")

    confidence = float(confidence)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-031 confidence outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-031 contradiction count invalid")

    body = {
        "source_entity_id": source_entity_id,
        "target_entity_id": target_entity_id,
        "relationship_type": relationship_type.strip(),
        "evidence_hashes": evidence,
        "confidence": confidence,
        "contradiction_count": contradiction_count,
        "directed": bool(directed),
    }

    request = OracleMemoryObservationRelationshipRequest(
        **body,
        request_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_relationship_request(request)
    return request


def verify_oracle_memory_observation_relationship_request(
    request: OracleMemoryObservationRelationshipRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-031 request hash mismatch")

    for value, label in (
        (request.source_entity_id, "source entity id"),
        (request.target_entity_id, "target entity id"),
        (request.request_hash, "request hash"),
    ):
        _require_hash(value, label)

    if request.source_entity_id == request.target_entity_id:
        _reject("OML-031 self relationship request")

    if not request.evidence_hashes:
        _reject("OML-031 request evidence missing")

    for value in request.evidence_hashes:
        _require_hash(value, "request evidence hash")

    if not 0.0 <= request.confidence <= 1.0:
        _reject("OML-031 request confidence invalid")

    if request.contradiction_count < 0:
        _reject("OML-031 request contradiction count invalid")

    return True


def _adapt_entity_resolution_batch(
    resolution: OracleMemoryObservationEntityResolution,
) -> OracleMemoryEntityResolutionBatch:
    verify_oracle_memory_observation_entity_resolution(resolution)

    body = {
        "schema_version": "OML-018",
        "engine_id": "OML-018",
        "policy_id": "oracle-memory.entity-resolution.v1",
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": "OML-017",
        "upstream_engine_id": "OML-017",
        "upstream_batch_hash": (
            resolution.upstream_validation_batch_hash
        ),
        "entities": resolution.entities,
        "resolved_entity_count": len(resolution.entities),
        "rejected_duplicate_count": resolution.rejected_duplicate_count,
        "canonical_order_verified": True,
        "deterministic_resolution_verified": True,
        "alias_normalization_verified": True,
        "entity_identity_uniqueness_verified": (
            resolution.entity_identity_uniqueness_verified
        ),
        "duplicate_candidates_excluded": (
            resolution.duplicate_candidates_excluded
        ),
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

    adapted = OracleMemoryEntityResolutionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    if any(
        not hasattr(entity, "__dataclass_fields__")
        for entity in adapted.entities
    ):
        _reject("OML-031 adapted entities lost dataclass identity")

    verify_oracle_memory_entity_resolution_batch(adapted)
    return adapted


def _build_binding(
    *,
    request: OracleMemoryObservationRelationshipRequest,
    relationship: OracleMemoryEntityRelationship,
    source_observation_hash: str,
    target_observation_hash: str,
) -> OracleMemoryObservationRelationshipBinding:
    verify_oracle_memory_observation_relationship_request(request)
    verify_oracle_memory_entity_relationship(relationship)

    body = {
        "request_hash": request.request_hash,
        "relationship_id": relationship.relationship_id,
        "relationship_hash": relationship.relationship_hash,
        "source_entity_id": relationship.source_entity_id,
        "target_entity_id": relationship.target_entity_id,
        "source_observation_hash": source_observation_hash,
        "target_observation_hash": target_observation_hash,
        "source_entity_lineage_verified": True,
        "target_entity_lineage_verified": True,
        "evidence_lineage_verified": (
            relationship.evidence_hashes == request.evidence_hashes
        ),
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    binding = OracleMemoryObservationRelationshipBinding(
        **body,
        binding_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_relationship_binding(binding)
    return binding


def verify_oracle_memory_observation_relationship_binding(
    binding: OracleMemoryObservationRelationshipBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-031 binding hash mismatch")

    for value, label in (
        (binding.request_hash, "request hash"),
        (binding.relationship_id, "relationship id"),
        (binding.relationship_hash, "relationship hash"),
        (binding.source_entity_id, "source entity id"),
        (binding.target_entity_id, "target entity id"),
        (binding.source_observation_hash, "source observation hash"),
        (binding.target_observation_hash, "target observation hash"),
        (binding.binding_hash, "binding hash"),
    ):
        _require_hash(value, label)

    required_true = (
        binding.source_entity_lineage_verified,
        binding.target_entity_lineage_verified,
        binding.evidence_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )

    if not all(required_true):
        _reject("OML-031 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-031 forbidden binding capability enabled")

    return True


def build_oracle_memory_observation_relationship_graph_materialization(
    *,
    resolution: OracleMemoryObservationEntityResolution,
    requests: Sequence[OracleMemoryObservationRelationshipRequest],
) -> OracleMemoryObservationRelationshipGraphMaterialization:
    verify_oracle_memory_observation_entity_resolution(resolution)

    if resolution.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-031 upstream schema mismatch")

    if resolution.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-031 upstream engine mismatch")

    if not resolution.resolution_ready:
        _reject("OML-031 upstream resolution not ready")

    if not resolution.downstream_relationship_graph_authorized:
        _reject("OML-031 graph materialization not authorized")

    if not resolution.read_only:
        _reject("OML-031 upstream resolution not read-only")

    adapted_batch = _adapt_entity_resolution_batch(resolution)

    entities_by_id = {
        entity.canonical_entity_id: entity
        for entity in resolution.entities
    }
    bindings_by_entity_id = {
        binding.canonical_entity_id: binding
        for binding in resolution.bindings
    }

    ordered_requests = tuple(
        sorted(
            requests,
            key=lambda item: (
                item.source_entity_id,
                item.target_entity_id,
                item.relationship_type,
                item.request_hash,
            ),
        )
    )

    relationships = []
    bindings = []

    for request in ordered_requests:
        verify_oracle_memory_observation_relationship_request(request)

        source_entity = entities_by_id.get(request.source_entity_id)
        target_entity = entities_by_id.get(request.target_entity_id)
        source_binding = bindings_by_entity_id.get(
            request.source_entity_id
        )
        target_binding = bindings_by_entity_id.get(
            request.target_entity_id
        )

        if (
            source_entity is None
            or target_entity is None
            or source_binding is None
            or target_binding is None
        ):
            _reject("OML-031 dangling observation relationship")

        relationship = build_oracle_memory_entity_relationship(
            source_entity=source_entity,
            target_entity=target_entity,
            relationship_type=request.relationship_type,
            evidence_hashes=request.evidence_hashes,
            confidence=request.confidence,
            contradiction_count=request.contradiction_count,
            directed=request.directed,
        )

        relationships.append(relationship)
        bindings.append(
            _build_binding(
                request=request,
                relationship=relationship,
                source_observation_hash=(
                    source_binding.observation_hash
                ),
                target_observation_hash=(
                    target_binding.observation_hash
                ),
            )
        )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=adapted_batch,
        relationships=tuple(relationships),
    )

    ordered_bindings = tuple(
        sorted(
            bindings,
            key=lambda item: (
                item.source_entity_id,
                item.target_entity_id,
                item.relationship_id,
                item.binding_hash,
            ),
        )
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": resolution.schema_version,
        "upstream_engine_id": resolution.engine_id,
        "upstream_resolution_hash": resolution.resolution_hash,
        "adapted_entity_batch_hash": adapted_batch.batch_hash,
        "relationship_graph_hash": graph.graph_hash,
        "graph": graph,
        "bindings": ordered_bindings,
        "entity_count": graph.entity_count,
        "relationship_count": graph.relationship_count,
        "graph_state": GRAPH_STATE_READ_ONLY,
        "certified_entity_lineage_verified": True,
        "observation_relationship_lineage_verified": True,
        "canonical_graph_order_verified": True,
        "deterministic_graph_materialization_verified": True,
        "dangling_relationships_rejected": True,
        "duplicate_relationships_rejected": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "graph_ready": True,
        "downstream_narrative_detection_authorized": True,
        "read_only": True,
    }

    materialization = (
        OracleMemoryObservationRelationshipGraphMaterialization(
            **body,
            materialization_hash=_stable_hash(body),
        )
    )

    verify_oracle_memory_observation_relationship_graph_materialization(
        materialization
    )
    return materialization


def verify_oracle_memory_observation_relationship_graph_materialization(
    materialization: (
        OracleMemoryObservationRelationshipGraphMaterialization
    ),
) -> bool:
    body = asdict(materialization)
    supplied = body.pop("materialization_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-031 materialization hash mismatch")

    if materialization.schema_version != SCHEMA_VERSION:
        _reject("OML-031 schema mismatch")

    if materialization.engine_id != ENGINE_ID:
        _reject("OML-031 engine mismatch")

    if materialization.policy_id != POLICY_ID:
        _reject("OML-031 policy mismatch")

    if materialization.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-031 subsystem mismatch")

    if materialization.upstream_schema_version != (
        UPSTREAM_SCHEMA_VERSION
    ):
        _reject("OML-031 upstream schema lineage mismatch")

    if materialization.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-031 upstream engine lineage mismatch")

    verify_oracle_memory_relationship_graph(materialization.graph)

    if materialization.entity_count != (
        materialization.graph.entity_count
    ):
        _reject("OML-031 entity count mismatch")

    if materialization.relationship_count != (
        materialization.graph.relationship_count
    ):
        _reject("OML-031 relationship count mismatch")

    if materialization.relationship_count != len(
        materialization.bindings
    ):
        _reject("OML-031 binding count mismatch")

    for binding in materialization.bindings:
        verify_oracle_memory_observation_relationship_binding(binding)

    if materialization.graph_state != GRAPH_STATE_READ_ONLY:
        _reject("OML-031 graph state invalid")

    required_true = (
        materialization.certified_entity_lineage_verified,
        materialization.observation_relationship_lineage_verified,
        materialization.canonical_graph_order_verified,
        materialization.deterministic_graph_materialization_verified,
        materialization.dangling_relationships_rejected,
        materialization.duplicate_relationships_rejected,
        materialization.graph_ready,
        materialization.downstream_narrative_detection_authorized,
        materialization.read_only,
    )

    if not all(required_true):
        _reject("OML-031 materialization guarantee missing")

    forbidden = (
        materialization.persistence_enabled,
        materialization.learning_updates_enabled,
        materialization.runtime_activation_enabled,
        materialization.publication_enabled,
        materialization.action_authorization_enabled,
        materialization.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-031 forbidden materialization capability enabled")

    return True
