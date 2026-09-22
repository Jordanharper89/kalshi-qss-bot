from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking import (
    OracleMemoryObservationNarrativeLifecycleTracking,
    verify_oracle_memory_observation_narrative_lifecycle_tracking,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import SUBSYSTEM_ID
from qseries_v2.oracle_memory.oracle_memory_source_reliability_memory import (
    OracleMemorySourceObservation,
    OracleMemorySourceReliabilityMemory,
    build_oracle_memory_source_observation,
    build_oracle_memory_source_reliability_memory,
    verify_oracle_memory_source_observation,
    verify_oracle_memory_source_reliability_memory,
)

SCHEMA_VERSION = "OML-034"
ENGINE_ID = "OML-034"
POLICY_ID = "oracle-memory.certified-observation-source-reliability-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-033"
UPSTREAM_ENGINE_ID = "OML-033"
STATE_READ_ONLY = "read_only_source_reliability"


class OracleMemoryCertifiedSourceReliabilityInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedSourceOutcome:
    source_name: str
    observation_hash: str
    outcome_confirmed: bool
    outcome_correct: bool
    contradiction_count: int
    confidence_at_observation: float
    observed_at: str
    outcome_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedSourceReliabilityBinding:
    source_id: str
    source_name: str
    profile_hash: str
    source_observation_hashes: tuple[str, ...]
    certified_observation_hashes: tuple[str, ...]
    lifecycle_tracking_hash: str
    source_identity_verified: bool
    observation_lineage_verified: bool
    lifecycle_lineage_verified: bool
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
class OracleMemoryCertifiedSourceReliability:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_tracking_hash: str
    upstream_lifecycle_memory_hash: str
    reliability_memory: OracleMemorySourceReliabilityMemory
    bindings: tuple[OracleMemoryCertifiedSourceReliabilityBinding, ...]
    source_count: int
    total_observation_count: int
    state: str
    certified_lifecycle_lineage_verified: bool
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
    memory_ready: bool
    downstream_calibration_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedSourceReliabilityInvariantError(
        f"unsupported OML-034 value type: {type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedSourceReliabilityInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-034 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedSourceReliabilityInvariantError(
            f"OML-034 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_source_outcome(
    *,
    source_name: str,
    observation_hash: str,
    outcome_confirmed: bool,
    outcome_correct: bool,
    contradiction_count: int,
    confidence_at_observation: float,
    observed_at: str,
) -> OracleMemoryCertifiedSourceOutcome:
    _require_hash(observation_hash, "observation hash")
    if not source_name.strip() or not observed_at.strip():
        _reject("OML-034 source name and observed_at required")
    if outcome_correct and not outcome_confirmed:
        _reject("OML-034 unconfirmed outcome cannot be correct")
    if contradiction_count < 0:
        _reject("OML-034 contradiction count invalid")
    confidence_at_observation = float(confidence_at_observation)
    if not 0.0 <= confidence_at_observation <= 1.0:
        _reject("OML-034 confidence outside [0, 1]")

    body = {
        "source_name": source_name.strip(),
        "observation_hash": observation_hash,
        "outcome_confirmed": bool(outcome_confirmed),
        "outcome_correct": bool(outcome_correct),
        "contradiction_count": contradiction_count,
        "confidence_at_observation": confidence_at_observation,
        "observed_at": observed_at.strip(),
    }
    outcome = OracleMemoryCertifiedSourceOutcome(**body, outcome_hash=_stable_hash(body))
    verify_oracle_memory_certified_source_outcome(outcome)
    return outcome


def verify_oracle_memory_certified_source_outcome(outcome: OracleMemoryCertifiedSourceOutcome) -> bool:
    body = asdict(outcome)
    supplied = body.pop("outcome_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-034 source outcome hash mismatch")
    _require_hash(outcome.observation_hash, "observation hash")
    _require_hash(outcome.outcome_hash, "outcome hash")
    if outcome.outcome_correct and not outcome.outcome_confirmed:
        _reject("OML-034 invalid outcome state")
    return True


def _build_binding(
    *,
    tracking: OracleMemoryObservationNarrativeLifecycleTracking,
    profile,
) -> OracleMemoryCertifiedSourceReliabilityBinding:
    certified_hashes = tuple(sorted(item.observation_hash for item in profile.observations))
    body = {
        "source_id": profile.source_id,
        "source_name": profile.source_name,
        "profile_hash": profile.profile_hash,
        "source_observation_hashes": tuple(item.source_observation_hash for item in profile.observations),
        "certified_observation_hashes": certified_hashes,
        "lifecycle_tracking_hash": tracking.tracking_hash,
        "source_identity_verified": True,
        "observation_lineage_verified": True,
        "lifecycle_lineage_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }
    binding = OracleMemoryCertifiedSourceReliabilityBinding(**body, binding_hash=_stable_hash(body))
    verify_oracle_memory_certified_source_reliability_binding(binding)
    return binding


def verify_oracle_memory_certified_source_reliability_binding(
    binding: OracleMemoryCertifiedSourceReliabilityBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-034 binding hash mismatch")
    for value in (
        binding.source_id,
        binding.profile_hash,
        binding.lifecycle_tracking_hash,
        binding.binding_hash,
        *binding.source_observation_hashes,
        *binding.certified_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")
    required = (
        binding.source_identity_verified,
        binding.observation_lineage_verified,
        binding.lifecycle_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )
    if not all(required):
        _reject("OML-034 binding guarantee missing")
    if any((
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )):
        _reject("OML-034 forbidden binding capability enabled")
    return True


def build_oracle_memory_certified_source_reliability(
    *,
    tracking: OracleMemoryObservationNarrativeLifecycleTracking,
    outcomes: Sequence[OracleMemoryCertifiedSourceOutcome],
) -> OracleMemoryCertifiedSourceReliability:
    verify_oracle_memory_observation_narrative_lifecycle_tracking(tracking)

    if tracking.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-034 upstream schema mismatch")
    if tracking.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-034 upstream engine mismatch")
    if not tracking.lifecycle_ready:
        _reject("OML-034 lifecycle tracking not ready")
    if not tracking.downstream_source_reliability_authorized:
        _reject("OML-034 source reliability not authorized")
    if not tracking.read_only:
        _reject("OML-034 upstream tracking not read-only")

    allowed_observation_hashes = {
        value
        for binding in tracking.bindings
        for value in binding.source_observation_hashes
    }

    observations_by_source: dict[str, list[OracleMemorySourceObservation]] = {}

    for outcome in outcomes:
        verify_oracle_memory_certified_source_outcome(outcome)
        if outcome.observation_hash not in allowed_observation_hashes:
            _reject("OML-034 outcome references unknown certified observation")

        source_observation = build_oracle_memory_source_observation(
            source_name=outcome.source_name,
            observation_hash=outcome.observation_hash,
            outcome_confirmed=outcome.outcome_confirmed,
            outcome_correct=outcome.outcome_correct,
            contradiction_count=outcome.contradiction_count,
            confidence_at_observation=outcome.confidence_at_observation,
            observed_at=outcome.observed_at,
        )
        observations_by_source.setdefault(outcome.source_name, []).append(source_observation)

    reliability_memory = build_oracle_memory_source_reliability_memory(
        lifecycle_memory=tracking.lifecycle_memory,
        observations_by_source={
            key: tuple(value)
            for key, value in observations_by_source.items()
        },
    )

    bindings = tuple(
        _build_binding(tracking=tracking, profile=profile)
        for profile in reliability_memory.profiles
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": tracking.schema_version,
        "upstream_engine_id": tracking.engine_id,
        "upstream_tracking_hash": tracking.tracking_hash,
        "upstream_lifecycle_memory_hash": tracking.lifecycle_memory.memory_hash,
        "reliability_memory": reliability_memory,
        "bindings": bindings,
        "source_count": reliability_memory.source_count,
        "total_observation_count": reliability_memory.total_observation_count,
        "state": STATE_READ_ONLY,
        "certified_lifecycle_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "deterministic_scoring_verified": reliability_memory.deterministic_scoring_verified,
        "source_identity_uniqueness_verified": reliability_memory.source_identity_uniqueness_verified,
        "contradiction_tracking_verified": reliability_memory.contradiction_tracking_verified,
        "calibration_tracking_verified": reliability_memory.calibration_tracking_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "downstream_calibration_authorized": True,
        "read_only": True,
    }

    result = OracleMemoryCertifiedSourceReliability(**body, certification_hash=_stable_hash(body))
    verify_oracle_memory_certified_source_reliability(result)
    return result


def verify_oracle_memory_certified_source_reliability(
    result: OracleMemoryCertifiedSourceReliability,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-034 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION or result.engine_id != ENGINE_ID:
        _reject("OML-034 identity mismatch")
    if result.policy_id != POLICY_ID or result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-034 policy/subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-034 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-034 upstream engine lineage mismatch")

    verify_oracle_memory_source_reliability_memory(result.reliability_memory)

    if result.source_count != len(result.bindings):
        _reject("OML-034 source/binding count mismatch")
    if result.source_count != result.reliability_memory.source_count:
        _reject("OML-034 source count mismatch")
    if result.total_observation_count != result.reliability_memory.total_observation_count:
        _reject("OML-034 observation count mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_source_reliability_binding(binding)

    required = (
        result.certified_lifecycle_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_scoring_verified,
        result.source_identity_uniqueness_verified,
        result.contradiction_tracking_verified,
        result.calibration_tracking_verified,
        result.memory_ready,
        result.downstream_calibration_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-034 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-034 state invalid")
    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-034 forbidden capability enabled")
    return True
