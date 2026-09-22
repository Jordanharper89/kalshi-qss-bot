from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking import (
    OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle,
    verify_oracle_memory_certified_market_behavior_narrative_lifecycle,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    OracleMemoryCertifiedSourceOutcome,
    OracleMemoryCertifiedSourceReliability,
    build_oracle_memory_certified_source_reliability,
    verify_oracle_memory_certified_source_outcome,
    verify_oracle_memory_certified_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-060"
ENGINE_ID = "OML-060"
POLICY_ID = "oracle-memory.certified-market-behavior-source-reliability.v1"
UPSTREAM_SCHEMA_VERSION = "OML-059"
UPSTREAM_ENGINE_ID = "OML-059"
RELIABILITY_SCHEMA_VERSION = "OML-034"
RELIABILITY_ENGINE_ID = "OML-034"
STATE_READ_ONLY = "read_only_market_behavior_source_reliability"


class OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorSourceReliability:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_lifecycle_tracking_hash: str
    reliability_schema_version: str
    reliability_engine_id: str
    source_reliability: OracleMemoryCertifiedSourceReliability
    source_count: int
    total_observation_count: int
    state: str
    lifecycle_lineage_verified: bool
    narrative_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_scoring_verified: bool
    source_identity_uniqueness_verified: bool
    contradiction_tracking_verified: bool
    calibration_tracking_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    reliability_ready: bool
    downstream_calibration_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(
        "unsupported OML-060 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-060 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError(
            f"OML-060 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_source_reliability(
    *,
    lifecycle: OracleMemoryCertifiedMarketBehaviorNarrativeLifecycle,
    outcomes: Sequence[OracleMemoryCertifiedSourceOutcome],
) -> OracleMemoryCertifiedMarketBehaviorSourceReliability:
    verify_oracle_memory_certified_market_behavior_narrative_lifecycle(lifecycle)

    if lifecycle.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-060 upstream schema mismatch")
    if lifecycle.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-060 upstream engine mismatch")
    if not lifecycle.lifecycle_ready:
        _reject("OML-060 upstream lifecycle not ready")
    if not lifecycle.downstream_source_reliability_authorized:
        _reject("OML-060 reliability continuation not authorized")
    if not lifecycle.read_only:
        _reject("OML-060 upstream lifecycle not read-only")

    allowed_hashes = {
        value
        for binding in lifecycle.lifecycle_tracking.bindings
        for value in binding.source_observation_hashes
    }
    if not allowed_hashes:
        _reject("OML-060 lifecycle contains no certified observations")

    for outcome in outcomes:
        verify_oracle_memory_certified_source_outcome(outcome)
        if outcome.observation_hash not in allowed_hashes:
            _reject("OML-060 outcome references unknown certified observation")

    reliability = build_oracle_memory_certified_source_reliability(
        tracking=lifecycle.lifecycle_tracking,
        outcomes=tuple(outcomes),
    )
    verify_oracle_memory_certified_source_reliability(reliability)

    if reliability.schema_version != RELIABILITY_SCHEMA_VERSION:
        _reject("OML-060 reliability schema mismatch")
    if reliability.engine_id != RELIABILITY_ENGINE_ID:
        _reject("OML-060 reliability engine mismatch")
    if reliability.upstream_tracking_hash != (
        lifecycle.lifecycle_tracking.tracking_hash
    ):
        _reject("OML-060 lifecycle-to-reliability lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": lifecycle.schema_version,
        "upstream_engine_id": lifecycle.engine_id,
        "upstream_certification_hash": lifecycle.certification_hash,
        "upstream_lifecycle_tracking_hash": (
            lifecycle.lifecycle_tracking.tracking_hash
        ),
        "reliability_schema_version": reliability.schema_version,
        "reliability_engine_id": reliability.engine_id,
        "source_reliability": reliability,
        "source_count": reliability.source_count,
        "total_observation_count": reliability.total_observation_count,
        "state": STATE_READ_ONLY,
        "lifecycle_lineage_verified": True,
        "narrative_lineage_verified": (
            lifecycle.observation_lifecycle_lineage_verified
        ),
        "certified_observation_lineage_verified": (
            reliability.certified_observation_lineage_verified
        ),
        "deterministic_scoring_verified": (
            reliability.deterministic_scoring_verified
        ),
        "source_identity_uniqueness_verified": (
            reliability.source_identity_uniqueness_verified
        ),
        "contradiction_tracking_verified": (
            reliability.contradiction_tracking_verified
        ),
        "calibration_tracking_verified": (
            reliability.calibration_tracking_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "reliability_ready": True,
        "downstream_calibration_authorized": (
            reliability.downstream_calibration_authorized
        ),
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorSourceReliability(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_source_reliability(result)
    return result


def verify_oracle_memory_certified_market_behavior_source_reliability(
    result: OracleMemoryCertifiedMarketBehaviorSourceReliability,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-060 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-060 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-060 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-060 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-060 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-060 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-060 upstream engine lineage mismatch")
    if result.reliability_schema_version != RELIABILITY_SCHEMA_VERSION:
        _reject("OML-060 reliability schema lineage mismatch")
    if result.reliability_engine_id != RELIABILITY_ENGINE_ID:
        _reject("OML-060 reliability engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_lifecycle_tracking_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_source_reliability(
        result.source_reliability
    )

    if result.upstream_lifecycle_tracking_hash != (
        result.source_reliability.upstream_tracking_hash
    ):
        _reject("OML-060 reliability lineage mismatch")
    if result.source_count != result.source_reliability.source_count:
        _reject("OML-060 source count mismatch")
    if result.total_observation_count != (
        result.source_reliability.total_observation_count
    ):
        _reject("OML-060 observation count mismatch")

    required = (
        result.lifecycle_lineage_verified,
        result.narrative_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_scoring_verified,
        result.source_identity_uniqueness_verified,
        result.contradiction_tracking_verified,
        result.calibration_tracking_verified,
        result.reliability_ready,
        result.downstream_calibration_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-060 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-060 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-060 forbidden capability enabled")

    return True
