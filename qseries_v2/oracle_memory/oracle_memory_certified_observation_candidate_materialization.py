from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    verify_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    OracleMemoryCanonicalRecordCandidate,
    build_oracle_memory_canonical_record_candidate,
    verify_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OracleMemoryCertifiedObservation,
    OracleMemoryObservationIntakeBatch,
    verify_oracle_memory_certified_observation,
    verify_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-028"
ENGINE_ID = "OML-028"
POLICY_ID = (
    "oracle-memory.certified-observation-candidate-materialization.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-027"
UPSTREAM_ENGINE_ID = "OML-027"

MATERIALIZATION_STATE_CONTRACT_ONLY = "contract_only"
MATERIALIZATION_STATUS_READY = "ready"
MATERIALIZATION_STATUS_DUPLICATE = "duplicate"


class OracleMemoryObservationMaterializationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationCandidateBinding:
    observation_hash: str
    observation_id: str
    candidate_hash: str
    candidate_id: str
    domain_id: str
    entity_key: str
    source_key: str
    materialization_status: str
    duplicate_of_candidate_hash: str | None
    observation_verified: bool
    candidate_verified: bool
    payload_lineage_verified: bool
    evidence_lineage_verified: bool
    parent_lineage_verified: bool
    source_certification_lineage_verified: bool
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
class OracleMemoryObservationCandidateMaterializationBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    upstream_gate_decision_hash: str
    candidates: tuple[OracleMemoryCanonicalRecordCandidate, ...]
    bindings: tuple[OracleMemoryObservationCandidateBinding, ...]
    observation_count: int
    candidate_count: int
    unique_candidate_count: int
    duplicate_candidate_count: int
    materialization_state: str
    canonical_order_verified: bool
    deterministic_materialization_verified: bool
    observation_candidate_lineage_verified: bool
    source_certification_lineage_verified: bool
    gate_decision_lineage_verified: bool
    duplicate_detection_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    materialization_ready: bool
    downstream_validation_authorized: bool
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

    raise OracleMemoryObservationMaterializationInvariantError(
        "unsupported OML-028 value type: "
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
    raise OracleMemoryObservationMaterializationInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-028 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationMaterializationInvariantError(
            f"OML-028 invalid {label} hexadecimal value"
        ) from exc


def _candidate_id_for(
    observation: OracleMemoryCertifiedObservation,
) -> str:
    return (
        "observation:"
        f"{observation.observation_kind}:"
        f"{observation.observation_id}"
    )


def _materialize_candidate(
    *,
    gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    observation: OracleMemoryCertifiedObservation,
) -> OracleMemoryCanonicalRecordCandidate:
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(
        gate_decision
    )
    verify_oracle_memory_certified_observation(observation)

    candidate = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate_decision,
        domain_id=observation.domain_id,
        candidate_id=_candidate_id_for(observation),
        entity_key=observation.entity_key,
        source_key=observation.source_key,
        observed_at=observation.observed_at,
        effective_at=observation.effective_at,
        payload={
            "observation_id": observation.observation_id,
            "observation_hash": observation.observation_hash,
            "observation_kind": observation.observation_kind,
            "observation_payload": observation.payload,
            "source_certification_hash": (
                observation.source_certification_hash
            ),
        },
        evidence_hashes=observation.evidence_hashes,
        parent_record_hashes=observation.parent_observation_hashes,
        confidence=observation.confidence,
        uncertainty=observation.uncertainty,
        contradiction_count=observation.contradiction_count,
    )

    verify_oracle_memory_canonical_record_candidate(candidate)

    if candidate.schema_version != "OML-009":
        _reject("OML-028 candidate schema lineage mismatch")

    if candidate.engine_id != "OML-009":
        _reject("OML-028 candidate engine lineage mismatch")

    if candidate.policy_id != (
        "oracle-memory.canonical-record-candidate-contract.v1"
    ):
        _reject("OML-028 candidate policy lineage mismatch")

    if candidate.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-028 candidate subsystem lineage mismatch")

    if candidate.upstream_gate_decision_hash != gate_decision.decision_hash:
        _reject("OML-028 gate decision lineage mismatch")

    if candidate.admission_authorized:
        _reject("OML-028 candidate admission must remain disabled")

    return candidate


def _build_binding(
    *,
    observation: OracleMemoryCertifiedObservation,
    candidate: OracleMemoryCanonicalRecordCandidate,
    duplicate_of_candidate_hash: str | None,
) -> OracleMemoryObservationCandidateBinding:
    verify_oracle_memory_certified_observation(observation)
    verify_oracle_memory_canonical_record_candidate(candidate)

    duplicate = duplicate_of_candidate_hash is not None

    body = {
        "observation_hash": observation.observation_hash,
        "observation_id": observation.observation_id,
        "candidate_hash": candidate.candidate_hash,
        "candidate_id": candidate.candidate_id,
        "domain_id": candidate.domain_id,
        "entity_key": candidate.entity_key,
        "source_key": candidate.source_key,
        "materialization_status": (
            MATERIALIZATION_STATUS_DUPLICATE
            if duplicate
            else MATERIALIZATION_STATUS_READY
        ),
        "duplicate_of_candidate_hash": duplicate_of_candidate_hash,
        "observation_verified": True,
        "candidate_verified": True,
        "payload_lineage_verified": (
            candidate.payload["observation_hash"]
            == observation.observation_hash
        ),
        "evidence_lineage_verified": (
            candidate.evidence_hashes == observation.evidence_hashes
        ),
        "parent_lineage_verified": (
            candidate.parent_record_hashes
            == observation.parent_observation_hashes
        ),
        "source_certification_lineage_verified": (
            candidate.payload["source_certification_hash"]
            == observation.source_certification_hash
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

    binding = OracleMemoryObservationCandidateBinding(
        **body,
        binding_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_binding(binding)
    return binding


def verify_oracle_memory_observation_candidate_binding(
    binding: OracleMemoryObservationCandidateBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-028 binding hash mismatch")

    for value, label in (
        (binding.observation_hash, "observation hash"),
        (binding.observation_id, "observation id"),
        (binding.candidate_hash, "candidate hash"),
        (binding.binding_hash, "binding hash"),
    ):
        _require_hash(value, label)

    if binding.materialization_status not in (
        MATERIALIZATION_STATUS_READY,
        MATERIALIZATION_STATUS_DUPLICATE,
    ):
        _reject("OML-028 materialization status invalid")

    if binding.materialization_status == MATERIALIZATION_STATUS_DUPLICATE:
        if binding.duplicate_of_candidate_hash is None:
            _reject("OML-028 duplicate candidate lineage missing")
        _require_hash(
            binding.duplicate_of_candidate_hash,
            "duplicate candidate hash",
        )
    elif binding.duplicate_of_candidate_hash is not None:
        _reject("OML-028 unexpected duplicate lineage")

    required_true = (
        binding.observation_verified,
        binding.candidate_verified,
        binding.payload_lineage_verified,
        binding.evidence_lineage_verified,
        binding.parent_lineage_verified,
        binding.source_certification_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )

    if not all(required_true):
        _reject("OML-028 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-028 forbidden binding capability enabled")

    return True


def build_oracle_memory_observation_candidate_materialization_batch(
    *,
    gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    intake_batch: OracleMemoryObservationIntakeBatch,
) -> OracleMemoryObservationCandidateMaterializationBatch:
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(
        gate_decision
    )
    verify_oracle_memory_observation_intake_batch(intake_batch)

    if intake_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-028 upstream schema mismatch")

    if intake_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-028 upstream engine mismatch")

    if not intake_batch.intake_ready:
        _reject("OML-028 upstream intake batch not ready")

    if not intake_batch.read_only:
        _reject("OML-028 upstream intake batch not read-only")

    ordered_observations = tuple(
        sorted(
            intake_batch.observations,
            key=lambda item: (
                item.domain_id,
                item.observed_at,
                item.entity_key,
                item.observation_id,
            ),
        )
    )

    candidates = tuple(
        _materialize_candidate(
            gate_decision=gate_decision,
            observation=observation,
        )
        for observation in ordered_observations
    )

    first_candidate_by_hash: dict[str, str] = {}
    bindings = []

    for observation, candidate in zip(
        ordered_observations,
        candidates,
        strict=True,
    ):
        duplicate_of = first_candidate_by_hash.get(
            candidate.candidate_hash
        )

        if duplicate_of is None:
            first_candidate_by_hash[
                candidate.candidate_hash
            ] = candidate.candidate_hash

        bindings.append(
            _build_binding(
                observation=observation,
                candidate=candidate,
                duplicate_of_candidate_hash=duplicate_of,
            )
        )

    binding_tuple = tuple(bindings)
    duplicate_count = sum(
        item.materialization_status
        == MATERIALIZATION_STATUS_DUPLICATE
        for item in binding_tuple
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": intake_batch.schema_version,
        "upstream_engine_id": intake_batch.engine_id,
        "upstream_batch_hash": intake_batch.batch_hash,
        "upstream_gate_decision_hash": gate_decision.decision_hash,
        "candidates": candidates,
        "bindings": binding_tuple,
        "observation_count": len(ordered_observations),
        "candidate_count": len(candidates),
        "unique_candidate_count": len(candidates) - duplicate_count,
        "duplicate_candidate_count": duplicate_count,
        "materialization_state": MATERIALIZATION_STATE_CONTRACT_ONLY,
        "canonical_order_verified": True,
        "deterministic_materialization_verified": True,
        "observation_candidate_lineage_verified": True,
        "source_certification_lineage_verified": True,
        "gate_decision_lineage_verified": True,
        "duplicate_detection_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "materialization_ready": True,
        "downstream_validation_authorized": True,
        "read_only": True,
    }

    batch = OracleMemoryObservationCandidateMaterializationBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_materialization_batch(
        batch
    )
    return batch


def verify_oracle_memory_observation_candidate_materialization_batch(
    batch: OracleMemoryObservationCandidateMaterializationBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-028 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-028 schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-028 engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-028 policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-028 subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-028 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-028 upstream engine lineage mismatch")

    _require_hash(
        batch.upstream_gate_decision_hash,
        "upstream gate decision hash",
    )

    if batch.observation_count != len(batch.bindings):
        _reject("OML-028 observation count mismatch")

    if batch.candidate_count != len(batch.candidates):
        _reject("OML-028 candidate count mismatch")

    if batch.candidate_count != batch.observation_count:
        _reject("OML-028 observation/candidate count mismatch")

    if (
        batch.unique_candidate_count
        + batch.duplicate_candidate_count
        != batch.candidate_count
    ):
        _reject("OML-028 duplicate count reconciliation mismatch")

    for candidate in batch.candidates:
        verify_oracle_memory_canonical_record_candidate(candidate)

        if candidate.schema_version != "OML-009":
            _reject("OML-028 candidate schema mismatch")

        if candidate.engine_id != "OML-009":
            _reject("OML-028 candidate engine mismatch")

        if candidate.upstream_gate_decision_hash != (
            batch.upstream_gate_decision_hash
        ):
            _reject("OML-028 candidate gate lineage mismatch")

        if candidate.admission_authorized:
            _reject("OML-028 candidate admission unexpectedly enabled")

    for binding in batch.bindings:
        verify_oracle_memory_observation_candidate_binding(binding)

    if batch.materialization_state != (
        MATERIALIZATION_STATE_CONTRACT_ONLY
    ):
        _reject("OML-028 materialization state invalid")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_materialization_verified,
        batch.observation_candidate_lineage_verified,
        batch.source_certification_lineage_verified,
        batch.gate_decision_lineage_verified,
        batch.duplicate_detection_verified,
        batch.materialization_ready,
        batch.downstream_validation_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-028 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-028 forbidden batch capability enabled")

    return True
