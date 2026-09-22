from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_narrative_detection_and_evolution import (
    OracleMemoryCertifiedCrossMarketNarrativeDetection,
    verify_oracle_memory_certified_cross_market_narrative_detection,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking import (
    OracleMemoryObservationNarrativeLifecycleTracking,
    build_oracle_memory_observation_narrative_lifecycle_tracking,
    verify_oracle_memory_observation_narrative_lifecycle_tracking,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    OracleMemoryNarrative,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-046"
ENGINE_ID = "OML-046"
POLICY_ID = (
    "oracle-memory."
    "certified-cross-market-narrative-lifecycle-tracking.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-045"
UPSTREAM_ENGINE_ID = "OML-045"
LIFECYCLE_SCHEMA_VERSION = "OML-033"
LIFECYCLE_ENGINE_ID = "OML-033"
STATE_READ_ONLY = "read_only_cross_market_narrative_lifecycle"


class OracleMemoryCertifiedCrossMarketLifecycleInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketNarrativeLifecycle:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_detection_hash: str
    lifecycle_schema_version: str
    lifecycle_engine_id: str
    lifecycle_tracking: OracleMemoryObservationNarrativeLifecycleTracking
    narrative_count: int
    snapshot_count: int
    transition_count: int
    state: str
    detection_lineage_verified: bool
    observation_lifecycle_lineage_verified: bool
    entity_lineage_preserved: bool
    relationship_lineage_preserved: bool
    canonical_temporal_order_verified: bool
    deterministic_lifecycle_tracking_verified: bool
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
    raise OracleMemoryCertifiedCrossMarketLifecycleInvariantError(
        "unsupported OML-046 value type"
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
    raise OracleMemoryCertifiedCrossMarketLifecycleInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-046 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketLifecycleInvariantError(
            f"OML-046 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_narrative_lifecycle(
    *,
    detection: OracleMemoryCertifiedCrossMarketNarrativeDetection,
    prior_histories: Mapping[str, Sequence[OracleMemoryNarrative]],
) -> OracleMemoryCertifiedCrossMarketNarrativeLifecycle:
    verify_oracle_memory_certified_cross_market_narrative_detection(detection)

    if detection.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-046 upstream schema mismatch")
    if detection.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-046 upstream engine mismatch")
    if not detection.detection_ready:
        _reject("OML-046 upstream detection not ready")
    if not detection.downstream_lifecycle_tracking_authorized:
        _reject("OML-046 lifecycle continuation not authorized")
    if not detection.read_only:
        _reject("OML-046 upstream detection not read-only")

    tracking = build_oracle_memory_observation_narrative_lifecycle_tracking(
        detection=detection.narrative_detection,
        prior_histories=prior_histories,
    )
    verify_oracle_memory_observation_narrative_lifecycle_tracking(tracking)

    if tracking.schema_version != LIFECYCLE_SCHEMA_VERSION:
        _reject("OML-046 lifecycle schema mismatch")
    if tracking.engine_id != LIFECYCLE_ENGINE_ID:
        _reject("OML-046 lifecycle engine mismatch")
    if tracking.upstream_detection_hash != (
        detection.narrative_detection.detection_hash
    ):
        _reject("OML-046 detection-to-lifecycle lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": detection.schema_version,
        "upstream_engine_id": detection.engine_id,
        "upstream_certification_hash": detection.certification_hash,
        "upstream_detection_hash": (
            detection.narrative_detection.detection_hash
        ),
        "lifecycle_schema_version": tracking.schema_version,
        "lifecycle_engine_id": tracking.engine_id,
        "lifecycle_tracking": tracking,
        "narrative_count": tracking.narrative_count,
        "snapshot_count": tracking.snapshot_count,
        "transition_count": tracking.transition_count,
        "state": STATE_READ_ONLY,
        "detection_lineage_verified": (
            tracking.certified_detection_lineage_verified
        ),
        "observation_lifecycle_lineage_verified": (
            tracking.observation_lifecycle_lineage_verified
        ),
        "entity_lineage_preserved": tracking.entity_lineage_preserved,
        "relationship_lineage_preserved": (
            tracking.relationship_lineage_preserved
        ),
        "canonical_temporal_order_verified": (
            tracking.canonical_temporal_order_verified
        ),
        "deterministic_lifecycle_tracking_verified": (
            tracking.deterministic_lifecycle_tracking_verified
        ),
        "evidence_growth_tracked": tracking.evidence_growth_tracked,
        "contradiction_growth_tracked": (
            tracking.contradiction_growth_tracked
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "lifecycle_ready": True,
        "downstream_source_reliability_authorized": (
            tracking.downstream_source_reliability_authorized
        ),
        "read_only": True,
    }

    result = OracleMemoryCertifiedCrossMarketNarrativeLifecycle(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_narrative_lifecycle(result)
    return result


def verify_oracle_memory_certified_cross_market_narrative_lifecycle(
    result: OracleMemoryCertifiedCrossMarketNarrativeLifecycle,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-046 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-046 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-046 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-046 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-046 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-046 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-046 upstream engine lineage mismatch")
    if result.lifecycle_schema_version != LIFECYCLE_SCHEMA_VERSION:
        _reject("OML-046 lifecycle schema lineage mismatch")
    if result.lifecycle_engine_id != LIFECYCLE_ENGINE_ID:
        _reject("OML-046 lifecycle engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_detection_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_narrative_lifecycle_tracking(
        result.lifecycle_tracking
    )

    if result.upstream_detection_hash != (
        result.lifecycle_tracking.upstream_detection_hash
    ):
        _reject("OML-046 lifecycle detection lineage mismatch")
    if result.narrative_count != result.lifecycle_tracking.narrative_count:
        _reject("OML-046 narrative count mismatch")
    if result.snapshot_count != result.lifecycle_tracking.snapshot_count:
        _reject("OML-046 snapshot count mismatch")
    if result.transition_count != result.lifecycle_tracking.transition_count:
        _reject("OML-046 transition count mismatch")

    required = (
        result.detection_lineage_verified,
        result.observation_lifecycle_lineage_verified,
        result.entity_lineage_preserved,
        result.relationship_lineage_preserved,
        result.canonical_temporal_order_verified,
        result.deterministic_lifecycle_tracking_verified,
        result.evidence_growth_tracked,
        result.contradiction_growth_tracked,
        result.lifecycle_ready,
        result.downstream_source_reliability_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-046 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-046 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-046 forbidden capability enabled")

    return True
