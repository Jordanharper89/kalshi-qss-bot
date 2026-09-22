from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_gate import (
    CONTINUATION_STATUS as ORR_012_CONTINUATION_STATUS,
    CONTINUATION_TYPE as ORR_012_CONTINUATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationActivationContinuation,
)

SCHEMA_VERSION = "ORR-013"
ENGINE_ID = "ORR-013"
POLICY_ID = "oracle.research-response.evidence-read-invocation-activation-continuation-attestation.v1"
ATTESTATION_TYPE = "oracle_research_response_evidence_read_invocation_activation_continuation_attestation"
ATTESTATION_STATUS = "oracle_research_response_evidence_read_invocation_activation_continuation_attested"


class OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation:
    attestation_id: str
    continuation_id: str
    continuation_hash: str
    activation_id: str
    activation_hash: str
    consumption_id: str
    consumption_hash: str
    authorization_id: str
    authorization_hash: str
    readiness_id: str
    readiness_hash: str
    evidence_admission_id: str
    evidence_admission_hash: str
    materialization_id: str
    materialization_hash: str
    plan_admission_id: str
    plan_admission_hash: str
    plan_id: str
    plan_hash: str
    admission_id: str
    admission_hash: str
    request_id: str
    request_hash: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_runtime_completion_id: str
    source_runtime_completion_hash: str
    subsystem_namespace: str
    requester_id: str
    correlation_id: str
    question_text: str
    response_mode: str
    filters: tuple[tuple[str, str], ...]
    requested_at: datetime
    admitted_at: datetime
    planned_at: datetime
    plan_admitted_at: datetime
    materialized_at: datetime
    evidence_admitted_at: datetime
    readiness_certified_at: datetime
    authorized_at: datetime
    consumed_at: datetime
    activated_at: datetime
    continuation_certified_at: datetime
    attested_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    activation_record_ids: tuple[str, ...]
    activation_record_hashes: tuple[str, ...]
    activated_invocation_ids: tuple[str, ...]
    activated_invocation_hashes: tuple[str, ...]
    activated_read_operations: tuple[str, ...]
    continuation_identity_verified: bool
    continuation_hash_verified: bool
    continuation_contract_verified: bool
    activation_record_identity_verified: bool
    activation_record_hashes_verified: bool
    invocation_lineage_verified: bool
    invocation_order_verified: bool
    invocation_count_verified: bool
    approved_read_operations_verified: bool
    attestation_scope_verified: bool
    callable_binding_remains_disabled_verified: bool
    callable_invocation_remains_disabled_verified: bool
    result_materialization_remains_disabled_verified: bool
    deterministic_boundary_verified: bool
    immutable_attestation_boundary_verified: bool
    read_only_boundary_verified: bool
    single_continuation_scope_verified: bool
    attestation_single_use_verified: bool
    duplicate_attestation_allowed: bool
    attestation_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    attestation_type: str
    attestation_status: str
    attestation_hash: str


class OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationGate:
    def attest(
        self,
        *,
        continuation: OracleResearchResponseEvidenceReadInvocationActivationContinuation,
        attested_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation:
        if not isinstance(
            continuation,
            OracleResearchResponseEvidenceReadInvocationActivationContinuation,
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
                "continuation must be canonical ORR-012 continuation"
            )

        continuation_body = asdict(continuation)
        supplied_hash = continuation_body.pop("continuation_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(continuation_body) != supplied_hash:
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
                "ORR-012 continuation hash mismatch"
            )

        required = (
            _valid_sha256(continuation.continuation_id),
            _valid_sha256(continuation.activation_id),
            _valid_sha256(continuation.activation_hash),
            _valid_sha256(continuation.consumption_id),
            _valid_sha256(continuation.consumption_hash),
            _valid_sha256(continuation.authorization_id),
            _valid_sha256(continuation.authorization_hash),
            _valid_sha256(continuation.readiness_id),
            _valid_sha256(continuation.readiness_hash),
            _valid_sha256(continuation.evidence_admission_id),
            _valid_sha256(continuation.evidence_admission_hash),
            _valid_sha256(continuation.materialization_id),
            _valid_sha256(continuation.materialization_hash),
            _valid_sha256(continuation.plan_admission_id),
            _valid_sha256(continuation.plan_admission_hash),
            _valid_sha256(continuation.plan_id),
            _valid_sha256(continuation.plan_hash),
            _valid_sha256(continuation.admission_id),
            _valid_sha256(continuation.admission_hash),
            _valid_sha256(continuation.request_id),
            _valid_sha256(continuation.request_hash),
            continuation.continuation_type == ORR_012_CONTINUATION_TYPE,
            continuation.continuation_status == ORR_012_CONTINUATION_STATUS,
            bool(continuation.activation_record_ids),
            len(continuation.activation_record_ids)
            == len(continuation.activation_record_hashes)
            == len(continuation.activated_invocation_ids)
            == len(continuation.activated_invocation_hashes)
            == len(continuation.activated_read_operations)
            == len(continuation.evidence_requirements),
            continuation.activation_identity_verified,
            continuation.activation_hash_verified,
            continuation.activation_contract_verified,
            continuation.activation_record_identity_verified,
            continuation.activation_record_hashes_verified,
            continuation.invocation_lineage_verified,
            continuation.invocation_order_verified,
            continuation.invocation_count_verified,
            continuation.approved_read_operations_verified,
            continuation.continuation_scope_verified,
            continuation.callable_binding_remains_disabled_verified,
            continuation.callable_invocation_remains_disabled_verified,
            continuation.result_materialization_remains_disabled_verified,
            continuation.deterministic_boundary_verified,
            continuation.immutable_continuation_boundary_verified,
            continuation.read_only_boundary_verified,
            continuation.single_activation_scope_verified,
            continuation.continuation_single_use_verified,
            not continuation.duplicate_continuation_allowed,
            not continuation.continuation_reversible,
        )
        forbidden = (
            continuation.runtime_serving_allowed,
            continuation.network_listener_allowed,
            continuation.database_connection_allowed,
            continuation.publication_allowed,
            continuation.qseries_handoff_allowed,
            continuation.qseries_execution_allowed,
            continuation.order_creation_allowed,
            continuation.funds_movement_allowed,
            continuation.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
                "ORR-012 continuation contract incomplete or unsafe"
            )

        collections = (
            continuation.activation_record_ids,
            continuation.activation_record_hashes,
            continuation.activated_invocation_ids,
            continuation.activated_invocation_hashes,
        )
        if (
            any(not all(_valid_sha256(value) for value in values) for values in collections)
            or len(set(continuation.activation_record_ids)) != len(continuation.activation_record_ids)
            or len(set(continuation.activated_invocation_ids)) != len(continuation.activated_invocation_ids)
            or not all(
                isinstance(value, str) and value
                for value in continuation.activated_read_operations
            )
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
                "continuation identities, hashes, operations, or uniqueness invalid"
            )

        if (
            not isinstance(attested_at, datetime)
            or attested_at.tzinfo is None
            or attested_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
                "attested_at must be timezone-aware"
            )
        at = attested_at.astimezone(timezone.utc)
        if at < continuation.continuation_certified_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError(
                "attestation cannot precede continuation certification"
            )

        body = {
            "continuation_id": continuation.continuation_id,
            "continuation_hash": continuation.continuation_hash,
            "activation_id": continuation.activation_id,
            "activation_hash": continuation.activation_hash,
            "consumption_id": continuation.consumption_id,
            "consumption_hash": continuation.consumption_hash,
            "authorization_id": continuation.authorization_id,
            "authorization_hash": continuation.authorization_hash,
            "readiness_id": continuation.readiness_id,
            "readiness_hash": continuation.readiness_hash,
            "evidence_admission_id": continuation.evidence_admission_id,
            "evidence_admission_hash": continuation.evidence_admission_hash,
            "materialization_id": continuation.materialization_id,
            "materialization_hash": continuation.materialization_hash,
            "plan_admission_id": continuation.plan_admission_id,
            "plan_admission_hash": continuation.plan_admission_hash,
            "plan_id": continuation.plan_id,
            "plan_hash": continuation.plan_hash,
            "admission_id": continuation.admission_id,
            "admission_hash": continuation.admission_hash,
            "request_id": continuation.request_id,
            "request_hash": continuation.request_hash,
            "dependency_receipt_id": continuation.dependency_receipt_id,
            "dependency_receipt_hash": continuation.dependency_receipt_hash,
            "source_runtime_completion_id": continuation.source_runtime_completion_id,
            "source_runtime_completion_hash": continuation.source_runtime_completion_hash,
            "subsystem_namespace": continuation.subsystem_namespace,
            "requester_id": continuation.requester_id,
            "correlation_id": continuation.correlation_id,
            "question_text": continuation.question_text,
            "response_mode": continuation.response_mode,
            "filters": continuation.filters,
            "requested_at": continuation.requested_at.astimezone(timezone.utc),
            "admitted_at": continuation.admitted_at.astimezone(timezone.utc),
            "planned_at": continuation.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": continuation.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": continuation.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": continuation.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": continuation.readiness_certified_at.astimezone(timezone.utc),
            "authorized_at": continuation.authorized_at.astimezone(timezone.utc),
            "consumed_at": continuation.consumed_at.astimezone(timezone.utc),
            "activated_at": continuation.activated_at.astimezone(timezone.utc),
            "continuation_certified_at": continuation.continuation_certified_at.astimezone(timezone.utc),
            "attested_at": at,
            "plan_steps": continuation.plan_steps,
            "evidence_requirements": continuation.evidence_requirements,
            "activation_record_ids": continuation.activation_record_ids,
            "activation_record_hashes": continuation.activation_record_hashes,
            "activated_invocation_ids": continuation.activated_invocation_ids,
            "activated_invocation_hashes": continuation.activated_invocation_hashes,
            "activated_read_operations": continuation.activated_read_operations,
            "continuation_identity_verified": True,
            "continuation_hash_verified": True,
            "continuation_contract_verified": True,
            "activation_record_identity_verified": True,
            "activation_record_hashes_verified": True,
            "invocation_lineage_verified": True,
            "invocation_order_verified": True,
            "invocation_count_verified": True,
            "approved_read_operations_verified": True,
            "attestation_scope_verified": True,
            "callable_binding_remains_disabled_verified": True,
            "callable_invocation_remains_disabled_verified": True,
            "result_materialization_remains_disabled_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_attestation_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_continuation_scope_verified": True,
            "attestation_single_use_verified": True,
            "duplicate_attestation_allowed": False,
            "attestation_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "attestation_type": ATTESTATION_TYPE,
            "attestation_status": ATTESTATION_STATUS,
        }
        body["attestation_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "continuation_id": continuation.continuation_id,
                "continuation_hash": continuation.continuation_hash,
                "attested_at": at,
                "activation_record_ids": continuation.activation_record_ids,
                "attestation_type": ATTESTATION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation(
            **body,
            attestation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ATTESTATION_TYPE",
    "ATTESTATION_STATUS",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationGate",
    "stable_hash",
]
