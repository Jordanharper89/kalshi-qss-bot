from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_attestation_gate import (
    ATTESTATION_STATUS as ORR_013_ATTESTATION_STATUS,
    ATTESTATION_TYPE as ORR_013_ATTESTATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation,
)

SCHEMA_VERSION = "ORR-014"
ENGINE_ID = "ORR-014"
POLICY_ID = "oracle.research-response.evidence-read-invocation-activation-continuation-attestation-consumption.v1"
CONSUMPTION_TYPE = "oracle_research_response_evidence_read_invocation_activation_continuation_attestation_consumption"
CONSUMPTION_STATUS = "oracle_research_response_evidence_read_invocation_activation_continuation_attestation_consumed"


class OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(ValueError):
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
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
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
class OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption:
    consumption_id: str
    attestation_id: str
    attestation_hash: str
    continuation_id: str
    continuation_hash: str
    activation_id: str
    activation_hash: str
    consumption_source_id: str
    consumption_source_hash: str
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
    attestation_consumed_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    activation_record_ids: tuple[str, ...]
    activation_record_hashes: tuple[str, ...]
    activated_invocation_ids: tuple[str, ...]
    activated_invocation_hashes: tuple[str, ...]
    activated_read_operations: tuple[str, ...]
    attestation_identity_verified: bool
    attestation_hash_verified: bool
    attestation_contract_verified: bool
    continuation_lineage_verified: bool
    activation_record_identity_verified: bool
    activation_record_hashes_verified: bool
    invocation_lineage_verified: bool
    invocation_order_verified: bool
    invocation_count_verified: bool
    approved_read_operations_verified: bool
    callable_binding_remains_disabled_verified: bool
    callable_invocation_remains_disabled_verified: bool
    result_materialization_remains_disabled_verified: bool
    deterministic_boundary_verified: bool
    immutable_consumption_boundary_verified: bool
    read_only_boundary_verified: bool
    single_attestation_scope_verified: bool
    consumption_single_use_verified: bool
    duplicate_consumption_allowed: bool
    consumption_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    consumption_type: str
    consumption_status: str
    consumption_hash: str


class OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionGate:
    def consume(
        self,
        *,
        attestation: OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation,
        attestation_consumed_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption:
        if not isinstance(
            attestation,
            OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation,
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
                "attestation must be canonical ORR-013 attestation"
            )

        attestation_body = asdict(attestation)
        supplied_hash = attestation_body.pop("attestation_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(attestation_body) != supplied_hash:
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
                "ORR-013 attestation hash mismatch"
            )

        required = (
            _valid_sha256(attestation.attestation_id),
            _valid_sha256(attestation.continuation_id),
            _valid_sha256(attestation.continuation_hash),
            _valid_sha256(attestation.activation_id),
            _valid_sha256(attestation.activation_hash),
            _valid_sha256(attestation.consumption_id),
            _valid_sha256(attestation.consumption_hash),
            _valid_sha256(attestation.authorization_id),
            _valid_sha256(attestation.authorization_hash),
            _valid_sha256(attestation.readiness_id),
            _valid_sha256(attestation.readiness_hash),
            _valid_sha256(attestation.evidence_admission_id),
            _valid_sha256(attestation.evidence_admission_hash),
            _valid_sha256(attestation.materialization_id),
            _valid_sha256(attestation.materialization_hash),
            _valid_sha256(attestation.plan_admission_id),
            _valid_sha256(attestation.plan_admission_hash),
            _valid_sha256(attestation.plan_id),
            _valid_sha256(attestation.plan_hash),
            _valid_sha256(attestation.admission_id),
            _valid_sha256(attestation.admission_hash),
            _valid_sha256(attestation.request_id),
            _valid_sha256(attestation.request_hash),
            attestation.attestation_type == ORR_013_ATTESTATION_TYPE,
            attestation.attestation_status == ORR_013_ATTESTATION_STATUS,
            bool(attestation.activation_record_ids),
            len(attestation.activation_record_ids)
            == len(attestation.activation_record_hashes)
            == len(attestation.activated_invocation_ids)
            == len(attestation.activated_invocation_hashes)
            == len(attestation.activated_read_operations)
            == len(attestation.evidence_requirements),
            attestation.continuation_identity_verified,
            attestation.continuation_hash_verified,
            attestation.continuation_contract_verified,
            attestation.activation_record_identity_verified,
            attestation.activation_record_hashes_verified,
            attestation.invocation_lineage_verified,
            attestation.invocation_order_verified,
            attestation.invocation_count_verified,
            attestation.approved_read_operations_verified,
            attestation.attestation_scope_verified,
            attestation.callable_binding_remains_disabled_verified,
            attestation.callable_invocation_remains_disabled_verified,
            attestation.result_materialization_remains_disabled_verified,
            attestation.deterministic_boundary_verified,
            attestation.immutable_attestation_boundary_verified,
            attestation.read_only_boundary_verified,
            attestation.single_continuation_scope_verified,
            attestation.attestation_single_use_verified,
            not attestation.duplicate_attestation_allowed,
            not attestation.attestation_reversible,
        )
        forbidden = (
            attestation.runtime_serving_allowed,
            attestation.network_listener_allowed,
            attestation.database_connection_allowed,
            attestation.publication_allowed,
            attestation.qseries_handoff_allowed,
            attestation.qseries_execution_allowed,
            attestation.order_creation_allowed,
            attestation.funds_movement_allowed,
            attestation.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
                "ORR-013 attestation contract incomplete or unsafe"
            )

        sha_collections = (
            attestation.activation_record_ids,
            attestation.activation_record_hashes,
            attestation.activated_invocation_ids,
            attestation.activated_invocation_hashes,
        )
        if (
            any(not all(_valid_sha256(value) for value in values) for values in sha_collections)
            or len(set(attestation.activation_record_ids)) != len(attestation.activation_record_ids)
            or len(set(attestation.activated_invocation_ids)) != len(attestation.activated_invocation_ids)
            or not all(
                isinstance(value, str) and value
                for value in attestation.activated_read_operations
            )
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
                "attested activation or invocation lineage invalid"
            )

        if (
            not isinstance(attestation_consumed_at, datetime)
            or attestation_consumed_at.tzinfo is None
            or attestation_consumed_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
                "attestation_consumed_at must be timezone-aware"
            )
        at = attestation_consumed_at.astimezone(timezone.utc)
        if at < attestation.attested_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError(
                "consumption cannot precede attestation"
            )

        body = {
            "attestation_id": attestation.attestation_id,
            "attestation_hash": attestation.attestation_hash,
            "continuation_id": attestation.continuation_id,
            "continuation_hash": attestation.continuation_hash,
            "activation_id": attestation.activation_id,
            "activation_hash": attestation.activation_hash,
            "consumption_source_id": attestation.consumption_id,
            "consumption_source_hash": attestation.consumption_hash,
            "authorization_id": attestation.authorization_id,
            "authorization_hash": attestation.authorization_hash,
            "readiness_id": attestation.readiness_id,
            "readiness_hash": attestation.readiness_hash,
            "evidence_admission_id": attestation.evidence_admission_id,
            "evidence_admission_hash": attestation.evidence_admission_hash,
            "materialization_id": attestation.materialization_id,
            "materialization_hash": attestation.materialization_hash,
            "plan_admission_id": attestation.plan_admission_id,
            "plan_admission_hash": attestation.plan_admission_hash,
            "plan_id": attestation.plan_id,
            "plan_hash": attestation.plan_hash,
            "admission_id": attestation.admission_id,
            "admission_hash": attestation.admission_hash,
            "request_id": attestation.request_id,
            "request_hash": attestation.request_hash,
            "dependency_receipt_id": attestation.dependency_receipt_id,
            "dependency_receipt_hash": attestation.dependency_receipt_hash,
            "source_runtime_completion_id": attestation.source_runtime_completion_id,
            "source_runtime_completion_hash": attestation.source_runtime_completion_hash,
            "subsystem_namespace": attestation.subsystem_namespace,
            "requester_id": attestation.requester_id,
            "correlation_id": attestation.correlation_id,
            "question_text": attestation.question_text,
            "response_mode": attestation.response_mode,
            "filters": attestation.filters,
            "requested_at": attestation.requested_at.astimezone(timezone.utc),
            "admitted_at": attestation.admitted_at.astimezone(timezone.utc),
            "planned_at": attestation.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": attestation.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": attestation.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": attestation.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": attestation.readiness_certified_at.astimezone(timezone.utc),
            "authorized_at": attestation.authorized_at.astimezone(timezone.utc),
            "consumed_at": attestation.consumed_at.astimezone(timezone.utc),
            "activated_at": attestation.activated_at.astimezone(timezone.utc),
            "continuation_certified_at": attestation.continuation_certified_at.astimezone(timezone.utc),
            "attested_at": attestation.attested_at.astimezone(timezone.utc),
            "attestation_consumed_at": at,
            "plan_steps": attestation.plan_steps,
            "evidence_requirements": attestation.evidence_requirements,
            "activation_record_ids": attestation.activation_record_ids,
            "activation_record_hashes": attestation.activation_record_hashes,
            "activated_invocation_ids": attestation.activated_invocation_ids,
            "activated_invocation_hashes": attestation.activated_invocation_hashes,
            "activated_read_operations": attestation.activated_read_operations,
            "attestation_identity_verified": True,
            "attestation_hash_verified": True,
            "attestation_contract_verified": True,
            "continuation_lineage_verified": True,
            "activation_record_identity_verified": True,
            "activation_record_hashes_verified": True,
            "invocation_lineage_verified": True,
            "invocation_order_verified": True,
            "invocation_count_verified": True,
            "approved_read_operations_verified": True,
            "callable_binding_remains_disabled_verified": True,
            "callable_invocation_remains_disabled_verified": True,
            "result_materialization_remains_disabled_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_consumption_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_attestation_scope_verified": True,
            "consumption_single_use_verified": True,
            "duplicate_consumption_allowed": False,
            "consumption_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "consumption_type": CONSUMPTION_TYPE,
            "consumption_status": CONSUMPTION_STATUS,
        }
        body["consumption_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "attestation_id": attestation.attestation_id,
                "attestation_hash": attestation.attestation_hash,
                "attestation_consumed_at": at,
                "activation_record_ids": attestation.activation_record_ids,
                "consumption_type": CONSUMPTION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption(
            **body,
            consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_TYPE",
    "CONSUMPTION_STATUS",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionGate",
    "stable_hash",
]
