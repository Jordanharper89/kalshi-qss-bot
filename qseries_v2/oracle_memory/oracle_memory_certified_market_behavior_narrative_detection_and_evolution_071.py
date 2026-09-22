from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_relationship_graph_070 import (
    OracleMemoryCertifiedMarketBehaviorRelationshipGraph070,
    verify_oracle_memory_certified_market_behavior_relationship_graph_070,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    OracleMemoryObservationNarrativeDetection,
    OracleMemoryObservationNarrativeRequest,
    build_oracle_memory_observation_narrative_detection,
    verify_oracle_memory_observation_narrative_detection,
    verify_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-071"
ENGINE_ID = "OML-071"
POLICY_ID = (
    "oracle-memory."
    "certified-market-behavior-narrative-detection-and-evolution-071.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-070"
UPSTREAM_ENGINE_ID = "OML-070"
NARRATIVE_SCHEMA_VERSION = "OML-032"
NARRATIVE_ENGINE_ID = "OML-032"
STATE_READ_ONLY = "read_only_market_behavior_narrative_detection_071"


class OracleMemoryCertifiedMarketBehaviorNarrative071InvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorNarrativeDetection071:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_graph_materialization_hash: str
    upstream_graph_hash: str
    narrative_schema_version: str
    narrative_engine_id: str
    narrative_detection: OracleMemoryObservationNarrativeDetection
    narrative_count: int
    emerging_count: int
    strengthening_count: int
    weakening_count: int
    resolved_count: int
    state: str
    graph_lineage_verified: bool
    observation_entity_lineage_verified: bool
    relationship_lineage_verified: bool
    observation_narrative_lineage_verified: bool
    canonical_order_verified: bool
    deterministic_detection_verified: bool
    contradiction_tracking_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    detection_ready: bool
    downstream_lifecycle_tracking_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorNarrative071InvariantError(
        "unsupported OML-071 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorNarrative071InvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-071 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorNarrative071InvariantError(
            f"OML-071 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_narrative_detection_071(
    *,
    graph: OracleMemoryCertifiedMarketBehaviorRelationshipGraph070,
    requests: Sequence[OracleMemoryObservationNarrativeRequest],
) -> OracleMemoryCertifiedMarketBehaviorNarrativeDetection071:
    verify_oracle_memory_certified_market_behavior_relationship_graph_070(graph)

    if graph.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-071 upstream schema mismatch")
    if graph.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-071 upstream engine mismatch")
    if not graph.graph_ready:
        _reject("OML-071 upstream graph not ready")
    if not graph.downstream_narrative_detection_authorized:
        _reject("OML-071 narrative continuation not authorized")
    if not graph.read_only:
        _reject("OML-071 upstream graph not read-only")

    for request in requests:
        verify_oracle_memory_observation_narrative_request(request)

    detection = build_oracle_memory_observation_narrative_detection(
        materialization=graph.graph_materialization,
        requests=tuple(requests),
    )
    verify_oracle_memory_observation_narrative_detection(detection)

    if detection.schema_version != NARRATIVE_SCHEMA_VERSION:
        _reject("OML-071 narrative schema mismatch")
    if detection.engine_id != NARRATIVE_ENGINE_ID:
        _reject("OML-071 narrative engine mismatch")
    if detection.upstream_materialization_hash != (
        graph.graph_materialization.materialization_hash
    ):
        _reject("OML-071 graph materialization lineage mismatch")
    if detection.upstream_graph_hash != (
        graph.graph_materialization.graph.graph_hash
    ):
        _reject("OML-071 graph hash lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": graph.schema_version,
        "upstream_engine_id": graph.engine_id,
        "upstream_certification_hash": graph.certification_hash,
        "upstream_graph_materialization_hash": (
            graph.graph_materialization.materialization_hash
        ),
        "upstream_graph_hash": graph.graph_materialization.graph.graph_hash,
        "narrative_schema_version": detection.schema_version,
        "narrative_engine_id": detection.engine_id,
        "narrative_detection": detection,
        "narrative_count": detection.narrative_count,
        "emerging_count": detection.emerging_count,
        "strengthening_count": detection.strengthening_count,
        "weakening_count": detection.weakening_count,
        "resolved_count": detection.resolved_count,
        "state": STATE_READ_ONLY,
        "graph_lineage_verified": True,
        "observation_entity_lineage_verified": (
            graph.observation_entity_lineage_verified
        ),
        "relationship_lineage_verified": graph.relationship_lineage_verified,
        "observation_narrative_lineage_verified": (
            detection.observation_narrative_lineage_verified
        ),
        "canonical_order_verified": detection.canonical_order_verified,
        "deterministic_detection_verified": (
            detection.deterministic_detection_verified
        ),
        "contradiction_tracking_verified": (
            detection.contradiction_tracking_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "detection_ready": True,
        "downstream_lifecycle_tracking_authorized": (
            detection.downstream_lifecycle_tracking_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedMarketBehaviorNarrativeDetection071(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_narrative_detection_071(result)
    return result


def verify_oracle_memory_certified_market_behavior_narrative_detection_071(
    result: OracleMemoryCertifiedMarketBehaviorNarrativeDetection071,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-071 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-071 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-071 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-071 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-071 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-071 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-071 upstream engine lineage mismatch")
    if result.narrative_schema_version != NARRATIVE_SCHEMA_VERSION:
        _reject("OML-071 narrative schema lineage mismatch")
    if result.narrative_engine_id != NARRATIVE_ENGINE_ID:
        _reject("OML-071 narrative engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_graph_materialization_hash,
        result.upstream_graph_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_narrative_detection(
        result.narrative_detection
    )

    if result.upstream_graph_materialization_hash != (
        result.narrative_detection.upstream_materialization_hash
    ):
        _reject("OML-071 materialization lineage mismatch")
    if result.upstream_graph_hash != (
        result.narrative_detection.upstream_graph_hash
    ):
        _reject("OML-071 graph lineage mismatch")
    if result.narrative_count != result.narrative_detection.narrative_count:
        _reject("OML-071 narrative count mismatch")
    if result.emerging_count != result.narrative_detection.emerging_count:
        _reject("OML-071 emerging count mismatch")
    if result.strengthening_count != (
        result.narrative_detection.strengthening_count
    ):
        _reject("OML-071 strengthening count mismatch")
    if result.weakening_count != result.narrative_detection.weakening_count:
        _reject("OML-071 weakening count mismatch")
    if result.resolved_count != result.narrative_detection.resolved_count:
        _reject("OML-071 resolved count mismatch")

    required = (
        result.graph_lineage_verified,
        result.observation_entity_lineage_verified,
        result.relationship_lineage_verified,
        result.observation_narrative_lineage_verified,
        result.canonical_order_verified,
        result.deterministic_detection_verified,
        result.contradiction_tracking_verified,
        result.detection_ready,
        result.downstream_lifecycle_tracking_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-071 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-071 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-071 forbidden capability enabled")

    return True
