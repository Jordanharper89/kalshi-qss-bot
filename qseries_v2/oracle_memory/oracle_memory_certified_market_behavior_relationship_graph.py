from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_entity_resolution import (
    OracleMemoryCertifiedMarketBehaviorEntityResolution,
    verify_oracle_memory_certified_market_behavior_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    OracleMemoryObservationRelationshipGraphMaterialization,
    OracleMemoryObservationRelationshipRequest,
    build_oracle_memory_observation_relationship_graph_materialization,
    verify_oracle_memory_observation_relationship_graph_materialization,
    verify_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-057"
ENGINE_ID = "OML-057"
POLICY_ID = "oracle-memory.certified-market-behavior-relationship-graph.v1"
UPSTREAM_SCHEMA_VERSION = "OML-056"
UPSTREAM_ENGINE_ID = "OML-056"
GRAPH_SCHEMA_VERSION = "OML-031"
GRAPH_ENGINE_ID = "OML-031"
STATE_READ_ONLY = "read_only_market_behavior_relationship_graph"


class OracleMemoryCertifiedMarketBehaviorRelationshipGraphInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorRelationshipGraph:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_resolution_hash: str
    graph_schema_version: str
    graph_engine_id: str
    graph_materialization: OracleMemoryObservationRelationshipGraphMaterialization
    entity_count: int
    relationship_count: int
    state: str
    resolution_lineage_verified: bool
    observation_entity_lineage_verified: bool
    relationship_lineage_verified: bool
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
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedMarketBehaviorRelationshipGraphInvariantError(
        "unsupported OML-057 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorRelationshipGraphInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-057 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorRelationshipGraphInvariantError(
            f"OML-057 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_relationship_graph(
    *,
    resolution: OracleMemoryCertifiedMarketBehaviorEntityResolution,
    requests: Sequence[OracleMemoryObservationRelationshipRequest],
) -> OracleMemoryCertifiedMarketBehaviorRelationshipGraph:
    verify_oracle_memory_certified_market_behavior_entity_resolution(resolution)

    if resolution.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-057 upstream schema mismatch")
    if resolution.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-057 upstream engine mismatch")
    if not resolution.resolution_ready:
        _reject("OML-057 upstream resolution not ready")
    if not resolution.downstream_relationship_graph_authorized:
        _reject("OML-057 relationship graph continuation not authorized")
    if not resolution.read_only:
        _reject("OML-057 upstream resolution not read-only")

    for request in requests:
        verify_oracle_memory_observation_relationship_request(request)

    graph_materialization = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution.resolution,
            requests=tuple(requests),
        )
    )
    verify_oracle_memory_observation_relationship_graph_materialization(
        graph_materialization
    )

    if graph_materialization.schema_version != GRAPH_SCHEMA_VERSION:
        _reject("OML-057 graph schema mismatch")
    if graph_materialization.engine_id != GRAPH_ENGINE_ID:
        _reject("OML-057 graph engine mismatch")
    if graph_materialization.upstream_resolution_hash != (
        resolution.resolution.resolution_hash
    ):
        _reject("OML-057 resolution-to-graph lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": resolution.schema_version,
        "upstream_engine_id": resolution.engine_id,
        "upstream_certification_hash": resolution.certification_hash,
        "upstream_resolution_hash": resolution.resolution.resolution_hash,
        "graph_schema_version": graph_materialization.schema_version,
        "graph_engine_id": graph_materialization.engine_id,
        "graph_materialization": graph_materialization,
        "entity_count": graph_materialization.entity_count,
        "relationship_count": graph_materialization.relationship_count,
        "state": STATE_READ_ONLY,
        "resolution_lineage_verified": True,
        "observation_entity_lineage_verified": (
            resolution.observation_entity_lineage_verified
        ),
        "relationship_lineage_verified": (
            graph_materialization.observation_relationship_lineage_verified
        ),
        "canonical_graph_order_verified": (
            graph_materialization.canonical_graph_order_verified
        ),
        "deterministic_graph_materialization_verified": (
            graph_materialization.deterministic_graph_materialization_verified
        ),
        "dangling_relationships_rejected": (
            graph_materialization.dangling_relationships_rejected
        ),
        "duplicate_relationships_rejected": (
            graph_materialization.duplicate_relationships_rejected
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "graph_ready": True,
        "downstream_narrative_detection_authorized": (
            graph_materialization.downstream_narrative_detection_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedMarketBehaviorRelationshipGraph(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_relationship_graph(result)
    return result


def verify_oracle_memory_certified_market_behavior_relationship_graph(
    result: OracleMemoryCertifiedMarketBehaviorRelationshipGraph,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-057 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-057 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-057 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-057 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-057 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-057 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-057 upstream engine lineage mismatch")
    if result.graph_schema_version != GRAPH_SCHEMA_VERSION:
        _reject("OML-057 graph schema lineage mismatch")
    if result.graph_engine_id != GRAPH_ENGINE_ID:
        _reject("OML-057 graph engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_resolution_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_relationship_graph_materialization(
        result.graph_materialization
    )

    if result.upstream_resolution_hash != (
        result.graph_materialization.upstream_resolution_hash
    ):
        _reject("OML-057 graph resolution lineage mismatch")
    if result.entity_count != result.graph_materialization.entity_count:
        _reject("OML-057 entity count mismatch")
    if result.relationship_count != (
        result.graph_materialization.relationship_count
    ):
        _reject("OML-057 relationship count mismatch")

    required = (
        result.resolution_lineage_verified,
        result.observation_entity_lineage_verified,
        result.relationship_lineage_verified,
        result.canonical_graph_order_verified,
        result.deterministic_graph_materialization_verified,
        result.dangling_relationships_rejected,
        result.duplicate_relationships_rejected,
        result.graph_ready,
        result.downstream_narrative_detection_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-057 guarantee missing")

    if result.state != STATE_READ_ONLY:
        _reject("OML-057 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-057 forbidden capability enabled")

    return True
