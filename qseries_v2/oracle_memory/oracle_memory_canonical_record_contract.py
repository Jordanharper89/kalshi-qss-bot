from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry_admission_gate import (
    OracleMemoryDomainRegistryAdmissionDecision,
    verify_oracle_memory_domain_registry_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-005"
ENGINE_ID = "OML-005"
POLICY_ID = "oracle-memory.canonical-record-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-004"
UPSTREAM_ENGINE_ID = "OML-004"

RECORD_STATE_CONTRACT_ONLY = "contract_only"


class OracleMemoryCanonicalRecordInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecord:
    schema_version: str
    contract_engine_id: str
    contract_policy_id: str
    subsystem_id: str
    upstream_admission_hash: str
    domain_id: str
    record_id: str
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
    record_state: str
    persistent_storage_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    record_hash: str


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordContractCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_admission_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    canonical_serialization_required: bool
    deterministic_record_hashing_required: bool
    immutable_record_identity_required: bool
    evidence_lineage_required: bool
    parent_lineage_supported: bool
    confidence_bounded: bool
    uncertainty_bounded: bool
    duplicate_evidence_hashes_forbidden: bool
    duplicate_parent_hashes_forbidden: bool
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
            raise OracleMemoryCanonicalRecordInvariantError(
                "OML-005 non-finite numeric value forbidden"
            )
        return value

    raise OracleMemoryCanonicalRecordInvariantError(
        "unsupported OML-005 value type: "
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
    raise OracleMemoryCanonicalRecordInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if len(value) != 64:
        _reject(f"OML-005 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCanonicalRecordInvariantError(
            f"OML-005 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_canonical_record(
    *,
    admission_decision: OracleMemoryDomainRegistryAdmissionDecision,
    domain_id: str,
    record_id: str,
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
) -> OracleMemoryCanonicalRecord:
    verify_oracle_memory_domain_registry_admission_decision(
        admission_decision
    )

    if admission_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-005 upstream schema mismatch")

    if admission_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-005 upstream engine mismatch")

    if not admission_decision.admitted:
        _reject("OML-005 upstream registry not admitted")

    if not admission_decision.next_certification_authorized:
        _reject("OML-005 upstream continuation not authorized")

    if domain_id not in admission_decision.admitted_domain_ids:
        _reject("OML-005 domain not certified")

    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-005 unknown memory domain")

    for label, value in (
        ("record_id", record_id),
        ("entity_key", entity_key),
        ("source_key", source_key),
        ("observed_at", observed_at),
        ("effective_at", effective_at),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"OML-005 {label} must be non-empty")

    if not isinstance(payload, Mapping):
        _reject("OML-005 payload must be a mapping")

    _canonical(payload)

    if not isinstance(confidence, (int, float)):
        _reject("OML-005 confidence must be numeric")

    if not isinstance(uncertainty, (int, float)):
        _reject("OML-005 uncertainty must be numeric")

    confidence = float(confidence)
    uncertainty = float(uncertainty)

    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        _reject("OML-005 confidence outside [0, 1]")

    if not math.isfinite(uncertainty) or not 0.0 <= uncertainty <= 1.0:
        _reject("OML-005 uncertainty outside [0, 1]")

    if (
        not isinstance(contradiction_count, int)
        or isinstance(contradiction_count, bool)
        or contradiction_count < 0
    ):
        _reject("OML-005 contradiction count invalid")

    if len(set(evidence_hashes)) != len(evidence_hashes):
        _reject("OML-005 duplicate evidence hashes forbidden")

    if len(set(parent_record_hashes)) != len(parent_record_hashes):
        _reject("OML-005 duplicate parent hashes forbidden")

    for value in evidence_hashes:
        _require_hash(value, "evidence hash")

    for value in parent_record_hashes:
        _require_hash(value, "parent record hash")

    body = {
        "schema_version": SCHEMA_VERSION,
        "contract_engine_id": ENGINE_ID,
        "contract_policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_admission_hash": admission_decision.decision_hash,
        "domain_id": domain_id,
        "record_id": record_id.strip(),
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": _canonical(payload),
        "evidence_hashes": tuple(evidence_hashes),
        "parent_record_hashes": tuple(parent_record_hashes),
        "confidence": confidence,
        "uncertainty": uncertainty,
        "contradiction_count": contradiction_count,
        "record_state": RECORD_STATE_CONTRACT_ONLY,
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    record = OracleMemoryCanonicalRecord(
        **body,
        record_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record(record)
    return record


def verify_oracle_memory_canonical_record(
    record: OracleMemoryCanonicalRecord,
) -> bool:
    body = asdict(record)
    supplied = body.pop("record_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-005 record hash mismatch")

    if record.schema_version != SCHEMA_VERSION:
        _reject("OML-005 record schema mismatch")

    if record.contract_engine_id != ENGINE_ID:
        _reject("OML-005 record engine mismatch")

    if record.contract_policy_id != POLICY_ID:
        _reject("OML-005 record policy mismatch")

    if record.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-005 record subsystem mismatch")

    _require_hash(record.upstream_admission_hash, "upstream admission hash")
    _require_hash(record.record_hash, "record hash")

    if record.domain_id not in MEMORY_DOMAINS:
        _reject("OML-005 record domain mismatch")

    for label, value in (
        ("record_id", record.record_id),
        ("entity_key", record.entity_key),
        ("source_key", record.source_key),
        ("observed_at", record.observed_at),
        ("effective_at", record.effective_at),
    ):
        if not value or value != value.strip():
            _reject(f"OML-005 record {label} invalid")

    _canonical(record.payload)

    if not math.isfinite(record.confidence):
        _reject("OML-005 record confidence not finite")

    if not 0.0 <= record.confidence <= 1.0:
        _reject("OML-005 record confidence outside [0, 1]")

    if not math.isfinite(record.uncertainty):
        _reject("OML-005 record uncertainty not finite")

    if not 0.0 <= record.uncertainty <= 1.0:
        _reject("OML-005 record uncertainty outside [0, 1]")

    if (
        not isinstance(record.contradiction_count, int)
        or isinstance(record.contradiction_count, bool)
        or record.contradiction_count < 0
    ):
        _reject("OML-005 record contradiction count invalid")

    if len(set(record.evidence_hashes)) != len(record.evidence_hashes):
        _reject("OML-005 record evidence hashes not unique")

    if len(set(record.parent_record_hashes)) != len(
        record.parent_record_hashes
    ):
        _reject("OML-005 record parent hashes not unique")

    for value in record.evidence_hashes:
        _require_hash(value, "record evidence hash")

    for value in record.parent_record_hashes:
        _require_hash(value, "record parent hash")

    if record.record_state != RECORD_STATE_CONTRACT_ONLY:
        _reject("OML-005 record state mismatch")

    forbidden = (
        record.persistent_storage_authorized,
        record.learning_update_authorized,
        record.runtime_activation_authorized,
        record.publication_authorized,
        record.action_authorization_enabled,
        record.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-005 forbidden record capability enabled")

    if not record.read_only:
        _reject("OML-005 record is not read-only")

    return True


def build_oracle_memory_canonical_record_contract_certification(
    *,
    admission_decision: OracleMemoryDomainRegistryAdmissionDecision,
) -> OracleMemoryCanonicalRecordContractCertification:
    verify_oracle_memory_domain_registry_admission_decision(
        admission_decision
    )

    if admission_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-005 certification upstream schema mismatch")

    if admission_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-005 certification upstream engine mismatch")

    if admission_decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-005 certification domain identity mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission_decision.schema_version,
        "upstream_engine_id": admission_decision.engine_id,
        "upstream_admission_hash": admission_decision.decision_hash,
        "upstream_registry_hash": admission_decision.upstream_registry_hash,
        "certified_domain_ids": admission_decision.admitted_domain_ids,
        "canonical_serialization_required": True,
        "deterministic_record_hashing_required": True,
        "immutable_record_identity_required": True,
        "evidence_lineage_required": True,
        "parent_lineage_supported": True,
        "confidence_bounded": True,
        "uncertainty_bounded": True,
        "duplicate_evidence_hashes_forbidden": True,
        "duplicate_parent_hashes_forbidden": True,
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

    certification = OracleMemoryCanonicalRecordContractCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_contract_certification(
        certification
    )
    return certification


def verify_oracle_memory_canonical_record_contract_certification(
    certification: OracleMemoryCanonicalRecordContractCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-005 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-005 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-005 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-005 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-005 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-005 admitted upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-005 admitted upstream engine mismatch")

    _require_hash(
        certification.upstream_admission_hash,
        "certification upstream admission hash",
    )
    _require_hash(
        certification.upstream_registry_hash,
        "certification upstream registry hash",
    )
    _require_hash(
        certification.certification_hash,
        "certification hash",
    )

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-005 certification domain mismatch")

    required_true = (
        certification.canonical_serialization_required,
        certification.deterministic_record_hashing_required,
        certification.immutable_record_identity_required,
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
        _reject("OML-005 certification guarantee missing")

    forbidden = (
        certification.persistent_storage_enabled,
        certification.learning_updates_enabled,
        certification.runtime_activation_enabled,
        certification.publication_enabled,
        certification.action_authorization_enabled,
        certification.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-005 forbidden certification capability enabled")

    return True
