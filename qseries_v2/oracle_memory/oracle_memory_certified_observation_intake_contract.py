from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    OracleMemoryCrossMarketDependencyMemory,
    verify_oracle_memory_cross_market_dependency_memory,
)

SCHEMA_VERSION = "OML-027"
ENGINE_ID = "OML-027"
POLICY_ID = "oracle-memory.certified-observation-intake-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-026"
UPSTREAM_ENGINE_ID = "OML-026"

OBSERVATION_STATE_CERTIFIED_INTAKE_ONLY = "certified_intake_only"
BATCH_STATE_CONTRACT_ONLY = "contract_only"

OBSERVATION_KIND_REAL_WORLD = "real_world"
OBSERVATION_KIND_MARKET = "market"
OBSERVATION_KIND_SOURCE = "source"
OBSERVATION_KIND_EVENT = "event"

ALLOWED_OBSERVATION_KINDS = (
    OBSERVATION_KIND_REAL_WORLD,
    OBSERVATION_KIND_MARKET,
    OBSERVATION_KIND_SOURCE,
    OBSERVATION_KIND_EVENT,
)


class OracleMemoryObservationIntakeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedObservation:
    observation_id: str
    observation_kind: str
    domain_id: str
    entity_key: str
    source_key: str
    observed_at: str
    effective_at: str
    payload: Mapping[str, Any]
    evidence_hashes: tuple[str, ...]
    parent_observation_hashes: tuple[str, ...]
    confidence: float
    uncertainty: float
    contradiction_count: int
    source_certification_hash: str
    observation_state: str
    deterministic_identity_verified: bool
    canonical_payload_verified: bool
    evidence_lineage_verified: bool
    parent_lineage_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    observation_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationIntakeBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_memory_hash: str
    observations: tuple[OracleMemoryCertifiedObservation, ...]
    observation_count: int
    unique_observation_count: int
    duplicate_observation_count: int
    batch_state: str
    canonical_order_verified: bool
    deterministic_hashing_verified: bool
    duplicate_detection_verified: bool
    evidence_lineage_verified: bool
    source_certification_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    intake_ready: bool
    candidate_materialization_authorized: bool
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

    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise OracleMemoryObservationIntakeInvariantError(
                "OML-027 non-finite number forbidden"
            )
        return value

    raise OracleMemoryObservationIntakeInvariantError(
        "unsupported OML-027 value type: "
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
    raise OracleMemoryObservationIntakeInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-027 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationIntakeInvariantError(
            f"OML-027 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_observation(
    *,
    observation_kind: str,
    domain_id: str,
    entity_key: str,
    source_key: str,
    observed_at: str,
    effective_at: str,
    payload: Mapping[str, Any],
    evidence_hashes: Sequence[str],
    source_certification_hash: str,
    parent_observation_hashes: Sequence[str] = (),
    confidence: float,
    uncertainty: float,
    contradiction_count: int = 0,
) -> OracleMemoryCertifiedObservation:
    if observation_kind not in ALLOWED_OBSERVATION_KINDS:
        _reject("OML-027 observation kind not allowed")

    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-027 unknown memory domain")

    for label, value in (
        ("entity_key", entity_key),
        ("source_key", source_key),
        ("observed_at", observed_at),
        ("effective_at", effective_at),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"OML-027 {label} must be non-empty")

    if not isinstance(payload, Mapping):
        _reject("OML-027 payload must be a mapping")

    canonical_payload = _canonical(payload)
    evidence = tuple(sorted(set(evidence_hashes)))
    parents = tuple(sorted(set(parent_observation_hashes)))

    if not evidence:
        _reject("OML-027 certified observation requires evidence")

    if len(evidence) != len(tuple(evidence_hashes)):
        _reject("OML-027 duplicate evidence hashes forbidden")

    if len(parents) != len(tuple(parent_observation_hashes)):
        _reject("OML-027 duplicate parent hashes forbidden")

    for value in evidence:
        _require_hash(value, "evidence hash")

    for value in parents:
        _require_hash(value, "parent observation hash")

    _require_hash(source_certification_hash, "source certification hash")

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        _reject("OML-027 confidence outside [0, 1]")

    if not math.isfinite(uncertainty) or not 0.0 <= uncertainty <= 1.0:
        _reject("OML-027 uncertainty outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-027 contradiction count invalid")

    identity = {
        "observation_kind": observation_kind,
        "domain_id": domain_id,
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": canonical_payload,
        "evidence_hashes": evidence,
        "parent_observation_hashes": parents,
        "source_certification_hash": source_certification_hash,
    }

    observation_id = _stable_hash(identity)

    body = {
        "observation_id": observation_id,
        "observation_kind": observation_kind,
        "domain_id": domain_id,
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": canonical_payload,
        "evidence_hashes": evidence,
        "parent_observation_hashes": parents,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "contradiction_count": contradiction_count,
        "source_certification_hash": source_certification_hash,
        "observation_state": OBSERVATION_STATE_CERTIFIED_INTAKE_ONLY,
        "deterministic_identity_verified": True,
        "canonical_payload_verified": True,
        "evidence_lineage_verified": True,
        "parent_lineage_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    observation = OracleMemoryCertifiedObservation(
        **body,
        observation_hash=_stable_hash(body),
    )

    verify_oracle_memory_certified_observation(observation)
    return observation


def verify_oracle_memory_certified_observation(
    observation: OracleMemoryCertifiedObservation,
) -> bool:
    body = asdict(observation)
    supplied = body.pop("observation_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-027 observation hash mismatch")

    for value, label in (
        (observation.observation_id, "observation id"),
        (observation.source_certification_hash, "source certification hash"),
        (observation.observation_hash, "observation hash"),
    ):
        _require_hash(value, label)

    if observation.observation_kind not in ALLOWED_OBSERVATION_KINDS:
        _reject("OML-027 observation kind invalid")

    if observation.domain_id not in MEMORY_DOMAINS:
        _reject("OML-027 observation domain invalid")

    if observation.observation_state != (
        OBSERVATION_STATE_CERTIFIED_INTAKE_ONLY
    ):
        _reject("OML-027 observation state invalid")

    if not observation.evidence_hashes:
        _reject("OML-027 evidence lineage missing")

    for value in (
        *observation.evidence_hashes,
        *observation.parent_observation_hashes,
    ):
        _require_hash(value, "observation lineage hash")

    if not 0.0 <= observation.confidence <= 1.0:
        _reject("OML-027 observation confidence invalid")

    if not 0.0 <= observation.uncertainty <= 1.0:
        _reject("OML-027 observation uncertainty invalid")

    if observation.contradiction_count < 0:
        _reject("OML-027 observation contradiction count invalid")

    required_true = (
        observation.deterministic_identity_verified,
        observation.canonical_payload_verified,
        observation.evidence_lineage_verified,
        observation.parent_lineage_verified,
        observation.read_only,
    )

    if not all(required_true):
        _reject("OML-027 observation guarantee missing")

    forbidden = (
        observation.persistence_authorized,
        observation.learning_update_authorized,
        observation.runtime_activation_authorized,
        observation.publication_authorized,
        observation.action_authorization_enabled,
        observation.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-027 forbidden observation capability enabled")

    return True


def build_oracle_memory_observation_intake_batch(
    *,
    cross_market_memory: OracleMemoryCrossMarketDependencyMemory,
    observations: Sequence[OracleMemoryCertifiedObservation],
) -> OracleMemoryObservationIntakeBatch:
    verify_oracle_memory_cross_market_dependency_memory(
        cross_market_memory
    )

    if cross_market_memory.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-027 upstream schema mismatch")

    if cross_market_memory.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-027 upstream engine mismatch")

    if not cross_market_memory.memory_ready:
        _reject("OML-027 upstream memory not ready")

    if not cross_market_memory.next_certification_authorized:
        _reject("OML-027 upstream continuation not authorized")

    if not cross_market_memory.read_only:
        _reject("OML-027 upstream memory not read-only")

    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (
                MEMORY_DOMAINS.index(item.domain_id),
                item.observed_at,
                item.entity_key,
                item.observation_id,
            ),
        )
    )

    for observation in ordered:
        verify_oracle_memory_certified_observation(observation)

    seen: set[str] = set()
    duplicate_count = 0

    for observation in ordered:
        if observation.observation_hash in seen:
            duplicate_count += 1
        else:
            seen.add(observation.observation_hash)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": cross_market_memory.schema_version,
        "upstream_engine_id": cross_market_memory.engine_id,
        "upstream_memory_hash": cross_market_memory.memory_hash,
        "observations": ordered,
        "observation_count": len(ordered),
        "unique_observation_count": len(seen),
        "duplicate_observation_count": duplicate_count,
        "batch_state": BATCH_STATE_CONTRACT_ONLY,
        "canonical_order_verified": True,
        "deterministic_hashing_verified": True,
        "duplicate_detection_verified": True,
        "evidence_lineage_verified": True,
        "source_certification_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "intake_ready": True,
        "candidate_materialization_authorized": False,
        "read_only": True,
    }

    batch = OracleMemoryObservationIntakeBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_intake_batch(batch)
    return batch


def verify_oracle_memory_observation_intake_batch(
    batch: OracleMemoryObservationIntakeBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-027 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-027 schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-027 engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-027 policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-027 subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-027 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-027 upstream engine lineage mismatch")

    if batch.observation_count != len(batch.observations):
        _reject("OML-027 observation count mismatch")

    if (
        batch.unique_observation_count
        + batch.duplicate_observation_count
        != batch.observation_count
    ):
        _reject("OML-027 duplicate reconciliation mismatch")

    for observation in batch.observations:
        verify_oracle_memory_certified_observation(observation)

    if batch.batch_state != BATCH_STATE_CONTRACT_ONLY:
        _reject("OML-027 batch state invalid")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_hashing_verified,
        batch.duplicate_detection_verified,
        batch.evidence_lineage_verified,
        batch.source_certification_verified,
        batch.intake_ready,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-027 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
        batch.candidate_materialization_authorized,
    )

    if any(forbidden):
        _reject("OML-027 forbidden batch capability enabled")

    return True
