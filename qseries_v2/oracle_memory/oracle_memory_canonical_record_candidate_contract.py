from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    verify_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-009"
ENGINE_ID = "OML-009"
POLICY_ID = "oracle-memory.canonical-record-candidate-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-008"
UPSTREAM_ENGINE_ID = "OML-008"

CANDIDATE_STATE_CONTRACT_ONLY = "candidate_contract_only"


class OracleMemoryCanonicalRecordCandidateInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordCandidate:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_gate_decision_hash: str
    domain_id: str
    candidate_id: str
    entity_key: str
    source_key: str
    observed_at: str
    effective_at: str
    payload: Mapping[str, Any]
    evidence_hashes: tuple[str, ...]
    parent_record_hashes: tuple[str, ...]
    confidence: float
    uncertainty: float
    contradiction_count: int
    candidate_state: str
    admission_authorized: bool
    persistent_storage_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    candidate_hash: str


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordCandidateContractCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_gate_decision_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    canonical_candidate_serialization_required: bool
    deterministic_candidate_hashing_required: bool
    immutable_candidate_identity_required: bool
    evidence_lineage_required: bool
    parent_lineage_supported: bool
    confidence_bounded: bool
    uncertainty_bounded: bool
    duplicate_evidence_hashes_forbidden: bool
    duplicate_parent_hashes_forbidden: bool
    candidate_admission_enabled: bool
    persistent_storage_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    contract_ready: bool
    next_certification_authorized: bool
    read_only: bool
    certification_hash: str


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
            raise OracleMemoryCanonicalRecordCandidateInvariantError(
                "OML-009 non-finite numeric value forbidden"
            )
        return value

    raise OracleMemoryCanonicalRecordCandidateInvariantError(
        "unsupported OML-009 value type: "
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
    raise OracleMemoryCanonicalRecordCandidateInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-009 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCanonicalRecordCandidateInvariantError(
            f"OML-009 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_canonical_record_candidate(
    *,
    gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    domain_id: str,
    candidate_id: str,
    entity_key: str,
    source_key: str,
    observed_at: str,
    effective_at: str,
    payload: Mapping[str, Any],
    evidence_hashes: tuple[str, ...] = (),
    parent_record_hashes: tuple[str, ...] = (),
    confidence: float,
    uncertainty: float,
    contradiction_count: int = 0,
) -> OracleMemoryCanonicalRecordCandidate:
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(
        gate_decision
    )

    if gate_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-009 upstream schema mismatch")

    if gate_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-009 upstream engine mismatch")

    if not gate_decision.admitted:
        _reject("OML-009 upstream registry gate not admitted")

    if not gate_decision.next_certification_authorized:
        _reject("OML-009 upstream continuation not authorized")

    if not gate_decision.read_only:
        _reject("OML-009 upstream read-only guarantee missing")

    if domain_id not in gate_decision.admitted_domain_ids:
        _reject("OML-009 domain not admitted")

    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-009 unknown memory domain")

    for label, value in (
        ("candidate_id", candidate_id),
        ("entity_key", entity_key),
        ("source_key", source_key),
        ("observed_at", observed_at),
        ("effective_at", effective_at),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"OML-009 {label} must be non-empty")

    if not isinstance(payload, Mapping):
        _reject("OML-009 payload must be a mapping")

    canonical_payload = _canonical(payload)

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        _reject("OML-009 confidence outside [0, 1]")

    if not math.isfinite(uncertainty) or not 0.0 <= uncertainty <= 1.0:
        _reject("OML-009 uncertainty outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-009 contradiction count invalid")

    if len(set(evidence_hashes)) != len(evidence_hashes):
        _reject("OML-009 duplicate evidence hashes forbidden")

    if len(set(parent_record_hashes)) != len(parent_record_hashes):
        _reject("OML-009 duplicate parent hashes forbidden")

    for value in evidence_hashes:
        _require_hash(value, "evidence hash")

    for value in parent_record_hashes:
        _require_hash(value, "parent record hash")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_gate_decision_hash": gate_decision.decision_hash,
        "domain_id": domain_id,
        "candidate_id": candidate_id.strip(),
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": canonical_payload,
        "evidence_hashes": tuple(evidence_hashes),
        "parent_record_hashes": tuple(parent_record_hashes),
        "confidence": confidence,
        "uncertainty": uncertainty,
        "contradiction_count": contradiction_count,
        "candidate_state": CANDIDATE_STATE_CONTRACT_ONLY,
        "admission_authorized": False,
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    candidate = OracleMemoryCanonicalRecordCandidate(
        **body,
        candidate_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_candidate(candidate)
    return candidate


def verify_oracle_memory_canonical_record_candidate(
    candidate: OracleMemoryCanonicalRecordCandidate,
) -> bool:
    body = asdict(candidate)
    supplied = body.pop("candidate_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-009 candidate hash mismatch")

    if candidate.schema_version != SCHEMA_VERSION:
        _reject("OML-009 candidate schema mismatch")

    if candidate.engine_id != ENGINE_ID:
        _reject("OML-009 candidate engine mismatch")

    if candidate.policy_id != POLICY_ID:
        _reject("OML-009 candidate policy mismatch")

    if candidate.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-009 candidate subsystem mismatch")

    _require_hash(
        candidate.upstream_gate_decision_hash,
        "upstream gate decision hash",
    )
    _require_hash(candidate.candidate_hash, "candidate hash")

    if candidate.domain_id not in MEMORY_DOMAINS:
        _reject("OML-009 candidate domain mismatch")

    if candidate.candidate_state != CANDIDATE_STATE_CONTRACT_ONLY:
        _reject("OML-009 candidate state mismatch")

    _canonical(candidate.payload)

    if not 0.0 <= candidate.confidence <= 1.0:
        _reject("OML-009 candidate confidence outside [0, 1]")

    if not 0.0 <= candidate.uncertainty <= 1.0:
        _reject("OML-009 candidate uncertainty outside [0, 1]")

    if candidate.contradiction_count < 0:
        _reject("OML-009 candidate contradiction count invalid")

    if len(set(candidate.evidence_hashes)) != len(
        candidate.evidence_hashes
    ):
        _reject("OML-009 duplicate evidence lineage")

    if len(set(candidate.parent_record_hashes)) != len(
        candidate.parent_record_hashes
    ):
        _reject("OML-009 duplicate parent lineage")

    forbidden = (
        candidate.admission_authorized,
        candidate.persistent_storage_authorized,
        candidate.learning_update_authorized,
        candidate.runtime_activation_authorized,
        candidate.publication_authorized,
        candidate.action_authorization_enabled,
        candidate.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-009 forbidden candidate capability enabled")

    if not candidate.read_only:
        _reject("OML-009 candidate is not read-only")

    return True


def build_oracle_memory_canonical_record_candidate_contract_certification(
    *,
    gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
) -> OracleMemoryCanonicalRecordCandidateContractCertification:
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(
        gate_decision
    )

    if gate_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-009 certification upstream schema mismatch")

    if gate_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-009 certification upstream engine mismatch")

    if gate_decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-009 certification domain identity mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": gate_decision.schema_version,
        "upstream_engine_id": gate_decision.engine_id,
        "upstream_gate_decision_hash": gate_decision.decision_hash,
        "upstream_registry_hash": gate_decision.upstream_registry_hash,
        "certified_domain_ids": gate_decision.admitted_domain_ids,
        "canonical_candidate_serialization_required": True,
        "deterministic_candidate_hashing_required": True,
        "immutable_candidate_identity_required": True,
        "evidence_lineage_required": True,
        "parent_lineage_supported": True,
        "confidence_bounded": True,
        "uncertainty_bounded": True,
        "duplicate_evidence_hashes_forbidden": True,
        "duplicate_parent_hashes_forbidden": True,
        "candidate_admission_enabled": False,
        "persistent_storage_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "contract_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    certification = OracleMemoryCanonicalRecordCandidateContractCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_candidate_contract_certification(
        certification
    )
    return certification


def verify_oracle_memory_canonical_record_candidate_contract_certification(
    certification: OracleMemoryCanonicalRecordCandidateContractCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-009 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-009 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-009 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-009 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-009 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-009 certification upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-009 certification upstream engine mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-009 certification domain mismatch")

    required_true = (
        certification.canonical_candidate_serialization_required,
        certification.deterministic_candidate_hashing_required,
        certification.immutable_candidate_identity_required,
        certification.evidence_lineage_required,
        certification.parent_lineage_supported,
        certification.confidence_bounded,
        certification.uncertainty_bounded,
        certification.duplicate_evidence_hashes_forbidden,
        certification.duplicate_parent_hashes_forbidden,
        certification.contract_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-009 certification guarantee missing")

    forbidden = (
        certification.candidate_admission_enabled,
        certification.persistent_storage_enabled,
        certification.learning_updates_enabled,
        certification.runtime_activation_enabled,
        certification.publication_enabled,
        certification.action_authorization_enabled,
        certification.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-009 forbidden certification capability enabled")

    return True
