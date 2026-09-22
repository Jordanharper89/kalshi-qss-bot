from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
    OracleMemoryNarrativeLifecycleMemory,
    verify_oracle_memory_narrative_lifecycle_memory,
)

SCHEMA_VERSION = "OML-022"
ENGINE_ID = "OML-022"
POLICY_ID = "oracle-memory.source-reliability-memory.v1"

UPSTREAM_SCHEMA_VERSION = "OML-021"
UPSTREAM_ENGINE_ID = "OML-021"

SOURCE_STATUS_UNPROVEN = "unproven"
SOURCE_STATUS_DEVELOPING = "developing"
SOURCE_STATUS_RELIABLE = "reliable"
SOURCE_STATUS_DEGRADED = "degraded"

ALLOWED_SOURCE_STATUSES = (
    SOURCE_STATUS_UNPROVEN,
    SOURCE_STATUS_DEVELOPING,
    SOURCE_STATUS_RELIABLE,
    SOURCE_STATUS_DEGRADED,
)


class OracleMemorySourceReliabilityInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemorySourceObservation:
    source_id: str
    source_name: str
    normalized_source_name: str
    observation_hash: str
    outcome_confirmed: bool
    outcome_correct: bool
    contradiction_count: int
    confidence_at_observation: float
    observed_at: str
    source_observation_hash: str


@dataclass(frozen=True)
class OracleMemorySourceReliabilityProfile:
    source_id: str
    source_name: str
    normalized_source_name: str
    source_status: str
    observations: tuple[OracleMemorySourceObservation, ...]
    observation_count: int
    confirmed_outcome_count: int
    correct_outcome_count: int
    incorrect_outcome_count: int
    unresolved_outcome_count: int
    contradiction_count: int
    reliability_score: float
    calibration_error: float
    evidence_depth: int
    deterministic_scoring_verified: bool
    canonical_order_verified: bool
    source_identity_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    profile_hash: str


@dataclass(frozen=True)
class OracleMemorySourceReliabilityMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_memory_hash: str
    profiles: tuple[OracleMemorySourceReliabilityProfile, ...]
    source_count: int
    total_observation_count: int
    deterministic_scoring_verified: bool
    source_identity_uniqueness_verified: bool
    canonical_source_order_verified: bool
    outcome_lineage_verified: bool
    contradiction_tracking_verified: bool
    calibration_tracking_verified: bool
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
    raise OracleMemorySourceReliabilityInvariantError(
        "unsupported OML-022 value type: "
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
    raise OracleMemorySourceReliabilityInvariantError(reason)


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())
    if not normalized:
        _reject("OML-022 source name cannot be empty")
    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-022 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemorySourceReliabilityInvariantError(
            f"OML-022 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_source_observation(
    *,
    source_name: str,
    observation_hash: str,
    outcome_confirmed: bool,
    outcome_correct: bool,
    contradiction_count: int,
    confidence_at_observation: float,
    observed_at: str,
) -> OracleMemorySourceObservation:
    normalized = _normalize(source_name)
    _require_hash(observation_hash, "observation hash")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-022 contradiction count invalid")

    confidence_at_observation = float(confidence_at_observation)
    if not 0.0 <= confidence_at_observation <= 1.0:
        _reject("OML-022 confidence outside [0, 1]")

    if outcome_correct and not outcome_confirmed:
        _reject("OML-022 unconfirmed outcome cannot be marked correct")

    if not isinstance(observed_at, str) or not observed_at.strip():
        _reject("OML-022 observed_at required")

    source_id = _stable_hash({"normalized_source_name": normalized})

    body = {
        "source_id": source_id,
        "source_name": source_name.strip(),
        "normalized_source_name": normalized,
        "observation_hash": observation_hash,
        "outcome_confirmed": bool(outcome_confirmed),
        "outcome_correct": bool(outcome_correct),
        "contradiction_count": contradiction_count,
        "confidence_at_observation": confidence_at_observation,
        "observed_at": observed_at.strip(),
    }

    observation = OracleMemorySourceObservation(
        **body,
        source_observation_hash=_stable_hash(body),
    )

    verify_oracle_memory_source_observation(observation)
    return observation


def verify_oracle_memory_source_observation(
    observation: OracleMemorySourceObservation,
) -> bool:
    body = asdict(observation)
    supplied = body.pop("source_observation_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-022 source observation hash mismatch")

    if observation.normalized_source_name != _normalize(
        observation.source_name
    ):
        _reject("OML-022 source normalization mismatch")

    expected_source_id = _stable_hash(
        {"normalized_source_name": observation.normalized_source_name}
    )

    if observation.source_id != expected_source_id:
        _reject("OML-022 source identity mismatch")

    _require_hash(observation.observation_hash, "observation hash")
    _require_hash(
        observation.source_observation_hash,
        "source observation hash",
    )

    if observation.outcome_correct and not observation.outcome_confirmed:
        _reject("OML-022 incorrect outcome state")

    if observation.contradiction_count < 0:
        _reject("OML-022 contradiction count invalid")

    if not 0.0 <= observation.confidence_at_observation <= 1.0:
        _reject("OML-022 observation confidence invalid")

    return True


def _status_for(
    *,
    observation_count: int,
    confirmed_count: int,
    reliability_score: float,
) -> str:
    if confirmed_count == 0:
        return SOURCE_STATUS_UNPROVEN

    if confirmed_count < 3:
        return SOURCE_STATUS_DEVELOPING

    if reliability_score >= 0.70:
        return SOURCE_STATUS_RELIABLE

    return SOURCE_STATUS_DEGRADED


def build_oracle_memory_source_reliability_profile(
    *,
    observations: Sequence[OracleMemorySourceObservation],
) -> OracleMemorySourceReliabilityProfile:
    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.observed_at,
                item.observation_hash,
                item.source_observation_hash,
            ),
        )
    )

    if not ordered:
        _reject("OML-022 source profile requires observations")

    for observation in ordered:
        verify_oracle_memory_source_observation(observation)

    source_ids = {item.source_id for item in ordered}
    if len(source_ids) != 1:
        _reject("OML-022 mixed sources in one profile")

    confirmed = tuple(
        item for item in ordered if item.outcome_confirmed
    )
    correct = tuple(
        item for item in confirmed if item.outcome_correct
    )

    confirmed_count = len(confirmed)
    correct_count = len(correct)
    incorrect_count = confirmed_count - correct_count
    unresolved_count = len(ordered) - confirmed_count
    contradictions = sum(
        item.contradiction_count for item in ordered
    )

    reliability_score = (
        round(correct_count / confirmed_count, 12)
        if confirmed_count
        else 0.5
    )

    calibration_error = (
        round(
            sum(
                abs(
                    item.confidence_at_observation
                    - (1.0 if item.outcome_correct else 0.0)
                )
                for item in confirmed
            )
            / confirmed_count,
            12,
        )
        if confirmed_count
        else 0.0
    )

    first = ordered[0]
    source_status = _status_for(
        observation_count=len(ordered),
        confirmed_count=confirmed_count,
        reliability_score=reliability_score,
    )

    body = {
        "source_id": first.source_id,
        "source_name": first.source_name,
        "normalized_source_name": first.normalized_source_name,
        "source_status": source_status,
        "observations": ordered,
        "observation_count": len(ordered),
        "confirmed_outcome_count": confirmed_count,
        "correct_outcome_count": correct_count,
        "incorrect_outcome_count": incorrect_count,
        "unresolved_outcome_count": unresolved_count,
        "contradiction_count": contradictions,
        "reliability_score": reliability_score,
        "calibration_error": calibration_error,
        "evidence_depth": len(ordered),
        "deterministic_scoring_verified": True,
        "canonical_order_verified": True,
        "source_identity_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    profile = OracleMemorySourceReliabilityProfile(
        **body,
        profile_hash=_stable_hash(body),
    )

    verify_oracle_memory_source_reliability_profile(profile)
    return profile


def verify_oracle_memory_source_reliability_profile(
    profile: OracleMemorySourceReliabilityProfile,
) -> bool:
    body = asdict(profile)
    supplied = body.pop("profile_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-022 profile hash mismatch")

    if profile.source_status not in ALLOWED_SOURCE_STATUSES:
        _reject("OML-022 source status invalid")

    if profile.observation_count != len(profile.observations):
        _reject("OML-022 observation count mismatch")

    if (
        profile.confirmed_outcome_count
        + profile.unresolved_outcome_count
        != profile.observation_count
    ):
        _reject("OML-022 confirmed/unresolved reconciliation mismatch")

    if (
        profile.correct_outcome_count
        + profile.incorrect_outcome_count
        != profile.confirmed_outcome_count
    ):
        _reject("OML-022 correct/incorrect reconciliation mismatch")

    for observation in profile.observations:
        verify_oracle_memory_source_observation(observation)

        if observation.source_id != profile.source_id:
            _reject("OML-022 profile source lineage mismatch")

    if not 0.0 <= profile.reliability_score <= 1.0:
        _reject("OML-022 reliability score invalid")

    if not 0.0 <= profile.calibration_error <= 1.0:
        _reject("OML-022 calibration error invalid")

    required_true = (
        profile.deterministic_scoring_verified,
        profile.canonical_order_verified,
        profile.source_identity_verified,
        profile.read_only,
    )

    if not all(required_true):
        _reject("OML-022 profile guarantee missing")

    forbidden = (
        profile.persistence_authorized,
        profile.learning_update_authorized,
        profile.runtime_activation_authorized,
        profile.publication_authorized,
        profile.action_authorization_enabled,
        profile.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-022 forbidden profile capability enabled")

    return True


def build_oracle_memory_source_reliability_memory(
    *,
    lifecycle_memory: OracleMemoryNarrativeLifecycleMemory,
    observations_by_source: Mapping[
        str,
        Sequence[OracleMemorySourceObservation],
    ],
) -> OracleMemorySourceReliabilityMemory:
    verify_oracle_memory_narrative_lifecycle_memory(
        lifecycle_memory
    )

    if lifecycle_memory.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-022 upstream schema mismatch")

    if lifecycle_memory.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-022 upstream engine mismatch")

    if not lifecycle_memory.memory_ready:
        _reject("OML-022 upstream lifecycle memory not ready")

    if not lifecycle_memory.next_certification_authorized:
        _reject("OML-022 upstream continuation not authorized")

    if not lifecycle_memory.read_only:
        _reject("OML-022 upstream lifecycle memory not read-only")

    profiles = tuple(
        sorted(
            (
                build_oracle_memory_source_reliability_profile(
                    observations=observations_by_source[source_name],
                )
                for source_name in sorted(
                    observations_by_source,
                    key=_normalize,
                )
            ),
            key=lambda item: (
                item.normalized_source_name,
                item.source_id,
            ),
        )
    )

    source_ids = tuple(profile.source_id for profile in profiles)

    if len(set(source_ids)) != len(source_ids):
        _reject("OML-022 duplicate source identities")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": lifecycle_memory.schema_version,
        "upstream_engine_id": lifecycle_memory.engine_id,
        "upstream_memory_hash": lifecycle_memory.memory_hash,
        "profiles": profiles,
        "source_count": len(profiles),
        "total_observation_count": sum(
            profile.observation_count for profile in profiles
        ),
        "deterministic_scoring_verified": True,
        "source_identity_uniqueness_verified": True,
        "canonical_source_order_verified": True,
        "outcome_lineage_verified": True,
        "contradiction_tracking_verified": True,
        "calibration_tracking_verified": True,
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

    memory = OracleMemorySourceReliabilityMemory(
        **body,
        memory_hash=_stable_hash(body),
    )

    verify_oracle_memory_source_reliability_memory(memory)
    return memory


def verify_oracle_memory_source_reliability_memory(
    memory: OracleMemorySourceReliabilityMemory,
) -> bool:
    body = asdict(memory)
    supplied = body.pop("memory_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-022 memory hash mismatch")

    if memory.schema_version != SCHEMA_VERSION:
        _reject("OML-022 schema mismatch")

    if memory.engine_id != ENGINE_ID:
        _reject("OML-022 engine mismatch")

    if memory.policy_id != POLICY_ID:
        _reject("OML-022 policy mismatch")

    if memory.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-022 subsystem mismatch")

    if memory.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-022 upstream schema lineage mismatch")

    if memory.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-022 upstream engine lineage mismatch")

    if memory.source_count != len(memory.profiles):
        _reject("OML-022 source count mismatch")

    if memory.total_observation_count != sum(
        profile.observation_count for profile in memory.profiles
    ):
        _reject("OML-022 total observation count mismatch")

    source_ids = []

    for profile in memory.profiles:
        verify_oracle_memory_source_reliability_profile(profile)
        source_ids.append(profile.source_id)

    if len(set(source_ids)) != len(source_ids):
        _reject("OML-022 duplicate profile identities")

    required_true = (
        memory.deterministic_scoring_verified,
        memory.source_identity_uniqueness_verified,
        memory.canonical_source_order_verified,
        memory.outcome_lineage_verified,
        memory.contradiction_tracking_verified,
        memory.calibration_tracking_verified,
        memory.memory_ready,
        memory.next_certification_authorized,
        memory.read_only,
    )

    if not all(required_true):
        _reject("OML-022 memory guarantee missing")

    forbidden = (
        memory.persistence_enabled,
        memory.learning_updates_enabled,
        memory.runtime_activation_enabled,
        memory.publication_enabled,
        memory.action_authorization_enabled,
        memory.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-022 forbidden memory capability enabled")

    return True
