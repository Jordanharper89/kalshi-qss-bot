from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_gate import (
    ACTIVATION_STATUS as ORR_011_ACTIVATION_STATUS,
    ACTIVATION_TYPE as ORR_011_ACTIVATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationActivation,
)

SCHEMA_VERSION = "ORR-012"
ENGINE_ID = "ORR-012"
POLICY_ID = "oracle.research-response.evidence-read-invocation-activation-continuation.v1"
CONTINUATION_TYPE = "oracle_research_response_evidence_read_invocation_activation_continuation"
CONTINUATION_STATUS = "oracle_research_response_evidence_read_invocation_activation_continuation_certified"


class OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(ValueError):
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
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
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
class OracleResearchResponseEvidenceReadInvocationActivationContinuation:
    continuation_id: str
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
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    activation_record_ids: tuple[str, ...]
    activation_record_hashes: tuple[str, ...]
    activated_invocation_ids: tuple[str, ...]
    activated_invocation_hashes: tuple[str, ...]
    activated_read_operations: tuple[str, ...]
    activation_identity_verified: bool
    activation_hash_verified: bool
    activation_contract_verified: bool
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
    single_activation_scope_verified: bool
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


class OracleResearchResponseEvidenceReadInvocationActivationContinuationGate:
    def certify(
        self,
        *,
        activation: OracleResearchResponseEvidenceReadInvocationActivation,
        continuation_certified_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationActivationContinuation:
        if not isinstance(
            activation,
            OracleResearchResponseEvidenceReadInvocationActivation,
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                "activation must be canonical ORR-011 activation"
            )

        activation_body = asdict(activation)
        supplied_hash = activation_body.pop("activation_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(activation_body) != supplied_hash:
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                "ORR-011 activation hash mismatch"
            )

        required = (
            _valid_sha256(activation.activation_id),
            _valid_sha256(activation.consumption_id),
            _valid_sha256(activation.consumption_hash),
            _valid_sha256(activation.authorization_id),
            _valid_sha256(activation.authorization_hash),
            _valid_sha256(activation.readiness_id),
            _valid_sha256(activation.readiness_hash),
            _valid_sha256(activation.evidence_admission_id),
            _valid_sha256(activation.evidence_admission_hash),
            _valid_sha256(activation.materialization_id),
            _valid_sha256(activation.materialization_hash),
            _valid_sha256(activation.plan_admission_id),
            _valid_sha256(activation.plan_admission_hash),
            _valid_sha256(activation.plan_id),
            _valid_sha256(activation.plan_hash),
            _valid_sha256(activation.admission_id),
            _valid_sha256(activation.admission_hash),
            _valid_sha256(activation.request_id),
            _valid_sha256(activation.request_hash),
            activation.activation_type == ORR_011_ACTIVATION_TYPE,
            activation.activation_status == ORR_011_ACTIVATION_STATUS,
            bool(activation.activated_invocations),
            len(activation.activated_invocations) == len(activation.evidence_requirements),
            activation.consumption_identity_verified,
            activation.consumption_hash_verified,
            activation.consumption_contract_verified,
            activation.invocation_lineage_verified,
            activation.invocation_hashes_verified,
            activation.invocation_order_verified,
            activation.invocation_count_verified,
            activation.approved_read_operations_verified,
            activation.activation_scope_verified,
            activation.callable_binding_remains_disabled_verified,
            activation.callable_invocation_remains_disabled_verified,
            activation.result_materialization_remains_disabled_verified,
            activation.deterministic_boundary_verified,
            activation.immutable_activation_boundary_verified,
            activation.read_only_boundary_verified,
            activation.single_consumption_scope_verified,
            activation.activation_single_use_verified,
            not activation.duplicate_activation_allowed,
            not activation.activation_reversible,
        )
        forbidden = (
            activation.runtime_serving_allowed,
            activation.network_listener_allowed,
            activation.database_connection_allowed,
            activation.publication_allowed,
            activation.qseries_handoff_allowed,
            activation.qseries_execution_allowed,
            activation.order_creation_allowed,
            activation.funds_movement_allowed,
            activation.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                "ORR-011 activation contract incomplete or unsafe"
            )

        activation_record_ids = []
        activation_record_hashes = []
        invocation_ids = []
        invocation_hashes = []
        read_operations = []
        expected_ordinals = tuple(range(1, len(activation.activated_invocations) + 1))

        for record in activation.activated_invocations:
            record_body = asdict(record)
            supplied_record_hash = record_body.pop("activation_record_hash", None)
            if (
                not _valid_sha256(record.activation_record_id)
                or not _valid_sha256(record.invocation_id)
                or not _valid_sha256(record.invocation_hash)
                or not _valid_sha256(supplied_record_hash)
                or stable_hash(record_body) != supplied_record_hash
                or not record.read_only
                or not record.activation_permitted
                or record.callable_bound
                or record.callable_invoked
                or record.result_materialized
                or record.external_side_effects_allowed
            ):
                raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                    "activation record invalid or unsafe"
                )
            activation_record_ids.append(record.activation_record_id)
            activation_record_hashes.append(record.activation_record_hash)
            invocation_ids.append(record.invocation_id)
            invocation_hashes.append(record.invocation_hash)
            read_operations.append(record.read_operation)

        ordinals = tuple(item.ordinal for item in activation.activated_invocations)
        if (
            ordinals != expected_ordinals
            or len(set(activation_record_ids)) != len(activation_record_ids)
            or len(set(invocation_ids)) != len(invocation_ids)
            or len(invocation_ids) != len(activation.evidence_requirements)
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                "activation identity, invocation identity, order, uniqueness, or count mismatch"
            )

        if (
            not isinstance(continuation_certified_at, datetime)
            or continuation_certified_at.tzinfo is None
            or continuation_certified_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                "continuation_certified_at must be timezone-aware"
            )
        at = continuation_certified_at.astimezone(timezone.utc)
        if at < activation.activated_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError(
                "continuation cannot precede activation"
            )

        body = {
            "activation_id": activation.activation_id,
            "activation_hash": activation.activation_hash,
            "consumption_id": activation.consumption_id,
            "consumption_hash": activation.consumption_hash,
            "authorization_id": activation.authorization_id,
            "authorization_hash": activation.authorization_hash,
            "readiness_id": activation.readiness_id,
            "readiness_hash": activation.readiness_hash,
            "evidence_admission_id": activation.evidence_admission_id,
            "evidence_admission_hash": activation.evidence_admission_hash,
            "materialization_id": activation.materialization_id,
            "materialization_hash": activation.materialization_hash,
            "plan_admission_id": activation.plan_admission_id,
            "plan_admission_hash": activation.plan_admission_hash,
            "plan_id": activation.plan_id,
            "plan_hash": activation.plan_hash,
            "admission_id": activation.admission_id,
            "admission_hash": activation.admission_hash,
            "request_id": activation.request_id,
            "request_hash": activation.request_hash,
            "dependency_receipt_id": activation.dependency_receipt_id,
            "dependency_receipt_hash": activation.dependency_receipt_hash,
            "source_runtime_completion_id": activation.source_runtime_completion_id,
            "source_runtime_completion_hash": activation.source_runtime_completion_hash,
            "subsystem_namespace": activation.subsystem_namespace,
            "requester_id": activation.requester_id,
            "correlation_id": activation.correlation_id,
            "question_text": activation.question_text,
            "response_mode": activation.response_mode,
            "filters": activation.filters,
            "requested_at": activation.requested_at.astimezone(timezone.utc),
            "admitted_at": activation.admitted_at.astimezone(timezone.utc),
            "planned_at": activation.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": activation.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": activation.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": activation.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": activation.readiness_certified_at.astimezone(timezone.utc),
            "authorized_at": activation.authorized_at.astimezone(timezone.utc),
            "consumed_at": activation.consumed_at.astimezone(timezone.utc),
            "activated_at": activation.activated_at.astimezone(timezone.utc),
            "continuation_certified_at": at,
            "plan_steps": activation.plan_steps,
            "evidence_requirements": activation.evidence_requirements,
            "activation_record_ids": tuple(activation_record_ids),
            "activation_record_hashes": tuple(activation_record_hashes),
            "activated_invocation_ids": tuple(invocation_ids),
            "activated_invocation_hashes": tuple(invocation_hashes),
            "activated_read_operations": tuple(read_operations),
            "activation_identity_verified": True,
            "activation_hash_verified": True,
            "activation_contract_verified": True,
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
            "single_activation_scope_verified": True,
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
                "activation_id": activation.activation_id,
                "activation_hash": activation.activation_hash,
                "continuation_certified_at": at,
                "activation_record_ids": tuple(activation_record_ids),
                "continuation_type": CONTINUATION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationActivationContinuation(
            **body,
            continuation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONTINUATION_TYPE",
    "CONTINUATION_STATUS",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuation",
    "OracleResearchResponseEvidenceReadInvocationActivationContinuationGate",
    "stable_hash",
]
