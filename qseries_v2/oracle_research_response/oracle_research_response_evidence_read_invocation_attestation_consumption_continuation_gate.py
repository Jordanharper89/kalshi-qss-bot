from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_attestation_consumption_gate import (
    CONSUMPTION_STATUS as ORR_014_CONSUMPTION_STATUS,
    CONSUMPTION_TYPE as ORR_014_CONSUMPTION_TYPE,
    OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption,
)

SCHEMA_VERSION = "ORR-015"
ENGINE_ID = "ORR-015"
POLICY_ID = "oracle.research-response.evidence-read-invocation-attestation-consumption-continuation.v1"
CONTINUATION_TYPE = "oracle_research_response_evidence_read_invocation_attestation_consumption_continuation"
CONTINUATION_STATUS = "oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_certified"


class OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(ValueError):
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
            raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
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
class OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuation:
    continuation_id: str
    consumption_id: str
    consumption_hash: str
    attestation_id: str
    attestation_hash: str
    continuation_source_id: str
    continuation_source_hash: str
    activation_id: str
    activation_hash: str
    authorization_consumption_id: str
    authorization_consumption_hash: str
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
    continuation_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    activation_record_ids: tuple[str, ...]
    activation_record_hashes: tuple[str, ...]
    activated_invocation_ids: tuple[str, ...]
    activated_invocation_hashes: tuple[str, ...]
    activated_read_operations: tuple[str, ...]
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_contract_verified: bool
    attestation_lineage_verified: bool
    activation_record_identity_verified: bool
    activation_record_hashes_verified: bool
    invocation_lineage_verified: bool
    invocation_order_verified: bool
    invocation_count_verified: bool
    approved_read_operations_verified: bool
    continuation_scope_verified: bool
    callable_binding_remains_disabled_verified: bool
    callable_invocation_remains_disabled_verified: bool
    result_materialization_remains_disabled_verified: bool
    deterministic_boundary_verified: bool
    immutable_continuation_boundary_verified: bool
    read_only_boundary_verified: bool
    single_consumption_scope_verified: bool
    continuation_single_use_verified: bool
    duplicate_continuation_allowed: bool
    continuation_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    continuation_type: str
    continuation_status: str
    continuation_hash: str


class OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationGate:
    def certify(
        self,
        *,
        consumption: OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption,
        continuation_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuation:
        if not isinstance(
            consumption,
            OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption,
        ):
            raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
                "consumption must be canonical ORR-014 consumption"
            )

        consumption_body = asdict(consumption)
        supplied_hash = consumption_body.pop("consumption_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(consumption_body) != supplied_hash:
            raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
                "ORR-014 consumption hash mismatch"
            )

        required = (
            _valid_sha256(consumption.consumption_id),
            _valid_sha256(consumption.attestation_id),
            _valid_sha256(consumption.attestation_hash),
            _valid_sha256(consumption.continuation_id),
            _valid_sha256(consumption.continuation_hash),
            _valid_sha256(consumption.activation_id),
            _valid_sha256(consumption.activation_hash),
            _valid_sha256(consumption.consumption_source_id),
            _valid_sha256(consumption.consumption_source_hash),
            _valid_sha256(consumption.authorization_id),
            _valid_sha256(consumption.authorization_hash),
            _valid_sha256(consumption.readiness_id),
            _valid_sha256(consumption.readiness_hash),
            _valid_sha256(consumption.evidence_admission_id),
            _valid_sha256(consumption.evidence_admission_hash),
            _valid_sha256(consumption.materialization_id),
            _valid_sha256(consumption.materialization_hash),
            _valid_sha256(consumption.plan_admission_id),
            _valid_sha256(consumption.plan_admission_hash),
            _valid_sha256(consumption.plan_id),
            _valid_sha256(consumption.plan_hash),
            _valid_sha256(consumption.admission_id),
            _valid_sha256(consumption.admission_hash),
            _valid_sha256(consumption.request_id),
            _valid_sha256(consumption.request_hash),
            consumption.consumption_type == ORR_014_CONSUMPTION_TYPE,
            consumption.consumption_status == ORR_014_CONSUMPTION_STATUS,
            bool(consumption.activation_record_ids),
            len(consumption.activation_record_ids)
            == len(consumption.activation_record_hashes)
            == len(consumption.activated_invocation_ids)
            == len(consumption.activated_invocation_hashes)
            == len(consumption.activated_read_operations)
            == len(consumption.evidence_requirements),
            consumption.attestation_identity_verified,
            consumption.attestation_hash_verified,
            consumption.attestation_contract_verified,
            consumption.continuation_lineage_verified,
            consumption.activation_record_identity_verified,
            consumption.activation_record_hashes_verified,
            consumption.invocation_lineage_verified,
            consumption.invocation_order_verified,
            consumption.invocation_count_verified,
            consumption.approved_read_operations_verified,
            consumption.callable_binding_remains_disabled_verified,
            consumption.callable_invocation_remains_disabled_verified,
            consumption.result_materialization_remains_disabled_verified,
            consumption.deterministic_boundary_verified,
            consumption.immutable_consumption_boundary_verified,
            consumption.read_only_boundary_verified,
            consumption.single_attestation_scope_verified,
            consumption.consumption_single_use_verified,
            not consumption.duplicate_consumption_allowed,
            not consumption.consumption_reversible,
        )
        forbidden = (
            consumption.runtime_serving_allowed,
            consumption.network_listener_allowed,
            consumption.database_connection_allowed,
            consumption.publication_allowed,
            consumption.qseries_handoff_allowed,
            consumption.qseries_execution_allowed,
            consumption.order_creation_allowed,
            consumption.funds_movement_allowed,
            consumption.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
                "ORR-014 consumption contract incomplete or unsafe"
            )

        sha_collections = (
            consumption.activation_record_ids,
            consumption.activation_record_hashes,
            consumption.activated_invocation_ids,
            consumption.activated_invocation_hashes,
        )
        if (
            any(not all(_valid_sha256(value) for value in values) for values in sha_collections)
            or len(set(consumption.activation_record_ids)) != len(consumption.activation_record_ids)
            or len(set(consumption.activated_invocation_ids)) != len(consumption.activated_invocation_ids)
            or not all(
                isinstance(value, str) and value
                for value in consumption.activated_read_operations
            )
        ):
            raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
                "consumption lineage identities, hashes, operations, or uniqueness invalid"
            )

        if (
            not isinstance(continuation_at, datetime)
            or continuation_at.tzinfo is None
            or continuation_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
                "continuation_at must be timezone-aware"
            )
        at = continuation_at.astimezone(timezone.utc)
        if at < consumption.attestation_consumed_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError(
                "continuation cannot precede attestation consumption"
            )

        body = {
            "consumption_id": consumption.consumption_id,
            "consumption_hash": consumption.consumption_hash,
            "attestation_id": consumption.attestation_id,
            "attestation_hash": consumption.attestation_hash,
            "continuation_source_id": consumption.continuation_id,
            "continuation_source_hash": consumption.continuation_hash,
            "activation_id": consumption.activation_id,
            "activation_hash": consumption.activation_hash,
            "authorization_consumption_id": consumption.consumption_source_id,
            "authorization_consumption_hash": consumption.consumption_source_hash,
            "authorization_id": consumption.authorization_id,
            "authorization_hash": consumption.authorization_hash,
            "readiness_id": consumption.readiness_id,
            "readiness_hash": consumption.readiness_hash,
            "evidence_admission_id": consumption.evidence_admission_id,
            "evidence_admission_hash": consumption.evidence_admission_hash,
            "materialization_id": consumption.materialization_id,
            "materialization_hash": consumption.materialization_hash,
            "plan_admission_id": consumption.plan_admission_id,
            "plan_admission_hash": consumption.plan_admission_hash,
            "plan_id": consumption.plan_id,
            "plan_hash": consumption.plan_hash,
            "admission_id": consumption.admission_id,
            "admission_hash": consumption.admission_hash,
            "request_id": consumption.request_id,
            "request_hash": consumption.request_hash,
            "dependency_receipt_id": consumption.dependency_receipt_id,
            "dependency_receipt_hash": consumption.dependency_receipt_hash,
            "source_runtime_completion_id": consumption.source_runtime_completion_id,
            "source_runtime_completion_hash": consumption.source_runtime_completion_hash,
            "subsystem_namespace": consumption.subsystem_namespace,
            "requester_id": consumption.requester_id,
            "correlation_id": consumption.correlation_id,
            "question_text": consumption.question_text,
            "response_mode": consumption.response_mode,
            "filters": consumption.filters,
            "requested_at": consumption.requested_at.astimezone(timezone.utc),
            "admitted_at": consumption.admitted_at.astimezone(timezone.utc),
            "planned_at": consumption.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": consumption.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": consumption.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": consumption.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": consumption.readiness_certified_at.astimezone(timezone.utc),
            "authorized_at": consumption.authorized_at.astimezone(timezone.utc),
            "consumed_at": consumption.consumed_at.astimezone(timezone.utc),
            "activated_at": consumption.activated_at.astimezone(timezone.utc),
            "continuation_certified_at": consumption.continuation_certified_at.astimezone(timezone.utc),
            "attested_at": consumption.attested_at.astimezone(timezone.utc),
            "attestation_consumed_at": consumption.attestation_consumed_at.astimezone(timezone.utc),
            "continuation_at": at,
            "plan_steps": consumption.plan_steps,
            "evidence_requirements": consumption.evidence_requirements,
            "activation_record_ids": consumption.activation_record_ids,
            "activation_record_hashes": consumption.activation_record_hashes,
            "activated_invocation_ids": consumption.activated_invocation_ids,
            "activated_invocation_hashes": consumption.activated_invocation_hashes,
            "activated_read_operations": consumption.activated_read_operations,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_contract_verified": True,
            "attestation_lineage_verified": True,
            "activation_record_identity_verified": True,
            "activation_record_hashes_verified": True,
            "invocation_lineage_verified": True,
            "invocation_order_verified": True,
            "invocation_count_verified": True,
            "approved_read_operations_verified": True,
            "continuation_scope_verified": True,
            "callable_binding_remains_disabled_verified": True,
            "callable_invocation_remains_disabled_verified": True,
            "result_materialization_remains_disabled_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_continuation_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_consumption_scope_verified": True,
            "continuation_single_use_verified": True,
            "duplicate_continuation_allowed": False,
            "continuation_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "continuation_type": CONTINUATION_TYPE,
            "continuation_status": CONTINUATION_STATUS,
        }
        body["continuation_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "consumption_id": consumption.consumption_id,
                "consumption_hash": consumption.consumption_hash,
                "continuation_at": at,
                "activation_record_ids": consumption.activation_record_ids,
                "continuation_type": CONTINUATION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuation(
            **body,
            continuation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONTINUATION_TYPE",
    "CONTINUATION_STATUS",
    "OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError",
    "OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuation",
    "OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationGate",
    "stable_hash",
]
