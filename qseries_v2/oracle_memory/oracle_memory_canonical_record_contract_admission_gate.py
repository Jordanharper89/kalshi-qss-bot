from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    ENGINE_ID as OML_005_ENGINE_ID,
    POLICY_ID as OML_005_POLICY_ID,
    SCHEMA_VERSION as OML_005_SCHEMA_VERSION,
    OracleMemoryCanonicalRecordContractCertification,
    verify_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-006"
ENGINE_ID = "OML-006"
POLICY_ID = "oracle-memory.canonical-record-contract-admission-gate.v1"

UPSTREAM_SCHEMA_VERSION = "OML-005"
UPSTREAM_ENGINE_ID = "OML-005"
UPSTREAM_POLICY_ID = "oracle-memory.canonical-record-contract.v1"

ADMISSION_STATUS_ADMITTED = "admitted"


class OracleMemoryCanonicalRecordContractAdmissionInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordContractAdmissionDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_certification_hash: str
    upstream_admission_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    contract_verified: bool
    upstream_identity_verified: bool
    upstream_lineage_verified: bool
    canonical_serialization_verified: bool
    deterministic_hashing_verified: bool
    immutable_identity_verified: bool
    evidence_lineage_verified: bool
    parent_lineage_verified: bool
    confidence_bounds_verified: bool
    uncertainty_bounds_verified: bool
    duplicate_evidence_rejection_verified: bool
    duplicate_parent_rejection_verified: bool
    persistent_storage_disabled_verified: bool
    learning_updates_disabled_verified: bool
    runtime_activation_disabled_verified: bool
    publication_disabled_verified: bool
    action_authorization_disabled_verified: bool
    qseries_execution_disabled_verified: bool
    upstream_continuation_authorized: bool
    admission_status: str
    admitted: bool
    next_certification_authorized: bool
    read_only: bool
    failure_reason: str | None
    decision_hash: str


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

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise OracleMemoryCanonicalRecordContractAdmissionInvariantError(
        "unsupported OML-006 value type: "
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
    raise OracleMemoryCanonicalRecordContractAdmissionInvariantError(
        reason
    )


def build_oracle_memory_canonical_record_contract_admission_decision(
    *,
    certification: OracleMemoryCanonicalRecordContractCertification,
) -> OracleMemoryCanonicalRecordContractAdmissionDecision:
    verify_oracle_memory_canonical_record_contract_certification(
        certification
    )

    if OML_005_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-006 upstream schema constant mismatch")

    if OML_005_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-006 upstream engine constant mismatch")

    if OML_005_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-006 upstream policy constant mismatch")

    if certification.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-006 upstream certification schema mismatch")

    if certification.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-006 upstream certification engine mismatch")

    if certification.policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-006 upstream certification policy mismatch")

    checks = {
        "contract_verified": True,
        "upstream_identity_verified": (
            certification.subsystem_id == SUBSYSTEM_ID
        ),
        "upstream_lineage_verified": all(
            len(value) == 64
            for value in (
                certification.certification_hash,
                certification.upstream_admission_hash,
                certification.upstream_registry_hash,
            )
        ),
        "canonical_serialization_verified": (
            certification.canonical_serialization_required
        ),
        "deterministic_hashing_verified": (
            certification.deterministic_record_hashing_required
        ),
        "immutable_identity_verified": (
            certification.immutable_record_identity_required
        ),
        "evidence_lineage_verified": (
            certification.evidence_lineage_required
        ),
        "parent_lineage_verified": (
            certification.parent_lineage_supported
        ),
        "confidence_bounds_verified": certification.confidence_bounded,
        "uncertainty_bounds_verified": certification.uncertainty_bounded,
        "duplicate_evidence_rejection_verified": (
            certification.duplicate_evidence_hashes_forbidden
        ),
        "duplicate_parent_rejection_verified": (
            certification.duplicate_parent_hashes_forbidden
        ),
        "persistent_storage_disabled_verified": (
            not certification.persistent_storage_enabled
        ),
        "learning_updates_disabled_verified": (
            not certification.learning_updates_enabled
        ),
        "runtime_activation_disabled_verified": (
            not certification.runtime_activation_enabled
        ),
        "publication_disabled_verified": (
            not certification.publication_enabled
        ),
        "action_authorization_disabled_verified": (
            not certification.action_authorization_enabled
        ),
        "qseries_execution_disabled_verified": (
            not certification.qseries_execution_enabled
        ),
        "upstream_continuation_authorized": (
            certification.next_certification_authorized
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        failed.append("certified_domain_ids")

    if not certification.contract_ready:
        failed.append("contract_ready")

    if not certification.read_only:
        failed.append("read_only")

    if failed:
        _reject(
            "OML-006 record contract admission failed: "
            + ", ".join(failed)
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": certification.schema_version,
        "upstream_engine_id": certification.engine_id,
        "upstream_policy_id": certification.policy_id,
        "upstream_certification_hash": certification.certification_hash,
        "upstream_admission_hash": certification.upstream_admission_hash,
        "upstream_registry_hash": certification.upstream_registry_hash,
        "certified_domain_ids": certification.certified_domain_ids,
        **checks,
        "admission_status": ADMISSION_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }

    decision = OracleMemoryCanonicalRecordContractAdmissionDecision(
        **body,
        decision_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_contract_admission_decision(
        decision
    )
    return decision


def verify_oracle_memory_canonical_record_contract_admission_decision(
    decision: OracleMemoryCanonicalRecordContractAdmissionDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-006 admission decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-006 schema mismatch")

    if decision.engine_id != ENGINE_ID:
        _reject("OML-006 engine mismatch")

    if decision.policy_id != POLICY_ID:
        _reject("OML-006 policy mismatch")

    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-006 subsystem mismatch")

    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-006 admitted upstream schema mismatch")

    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-006 admitted upstream engine mismatch")

    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-006 admitted upstream policy mismatch")

    hashes = (
        decision.upstream_certification_hash,
        decision.upstream_admission_hash,
        decision.upstream_registry_hash,
        decision.decision_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-006 lineage hash length invalid")

    if decision.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-006 admitted domain identity mismatch")

    required_true = (
        decision.contract_verified,
        decision.upstream_identity_verified,
        decision.upstream_lineage_verified,
        decision.canonical_serialization_verified,
        decision.deterministic_hashing_verified,
        decision.immutable_identity_verified,
        decision.evidence_lineage_verified,
        decision.parent_lineage_verified,
        decision.confidence_bounds_verified,
        decision.uncertainty_bounds_verified,
        decision.duplicate_evidence_rejection_verified,
        decision.duplicate_parent_rejection_verified,
        decision.persistent_storage_disabled_verified,
        decision.learning_updates_disabled_verified,
        decision.runtime_activation_disabled_verified,
        decision.publication_disabled_verified,
        decision.action_authorization_disabled_verified,
        decision.qseries_execution_disabled_verified,
        decision.upstream_continuation_authorized,
        decision.admitted,
        decision.next_certification_authorized,
        decision.read_only,
    )

    if not all(required_true):
        _reject("OML-006 admitted decision missing required guarantee")

    if decision.admission_status != ADMISSION_STATUS_ADMITTED:
        _reject("OML-006 admission status mismatch")

    if decision.failure_reason is not None:
        _reject("OML-006 admitted decision contains failure reason")

    return True
