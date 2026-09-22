from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_gate import (
    CONTINUATION_STATUS as OOR_011_CONTINUATION_STATUS,
    CONTINUATION_TYPE as OOR_011_CONTINUATION_TYPE,
    OracleOperatorRuntimeSessionActivationContinuation,
)

SCHEMA_VERSION = "OOR-012"
ENGINE_ID = "OOR-012"
POLICY_ID = "oracle.operator-runtime-session-activation-continuation-attestation-gate.v1"
ATTESTATION_TYPE = "oracle_operator_runtime_read_only_session_activation_continuation_attestation"
ATTESTATION_STATUS = "oracle_operator_runtime_session_activation_continuation_attested"


class OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
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
class OracleOperatorRuntimeSessionActivationContinuationAttestation:
    attestation_id: str
    continuation_id: str
    continuation_hash: str
    authorization_consumption_id: str
    authorization_consumption_hash: str
    activation_authorization_id: str
    activation_authorization_hash: str
    attestation_source_id: str
    attestation_source_hash: str
    activation_id: str
    activation_hash: str
    session_authorization_consumption_id: str
    session_authorization_consumption_hash: str
    session_authorization_id: str
    session_authorization_hash: str
    session_id: str
    session_hash: str
    admission_id: str
    admission_hash: str
    request_id: str
    request_hash: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_operator_completion_certification_id: str
    runtime_namespace: str
    requester_id: str
    correlation_id: str
    mode: str
    query_text: str
    requested_at: datetime
    admitted_at: datetime
    assembled_at: datetime
    session_authorized_at: datetime
    session_authorization_consumed_at: datetime
    activated_at: datetime
    activation_attested_at: datetime
    activation_authorized_at: datetime
    activation_authorization_consumed_at: datetime
    continued_at: datetime
    continuation_attested_at: datetime
    continuation_identity_verified: bool
    continuation_hash_verified: bool
    continuation_contract_verified: bool
    complete_runtime_lineage_verified: bool
    single_continuation_scope_verified: bool
    single_attestation_scope_verified: bool
    attestation_single_use_verified: bool
    read_only_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_result_boundary_verified: bool
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


class OracleOperatorRuntimeSessionActivationContinuationAttestationGate:
    def attest(
        self,
        *,
        continuation: OracleOperatorRuntimeSessionActivationContinuation,
        attested_at: datetime,
    ) -> OracleOperatorRuntimeSessionActivationContinuationAttestation:
        if not isinstance(continuation, OracleOperatorRuntimeSessionActivationContinuation):
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "continuation must be canonical OOR-011 continuation"
            )

        body = asdict(continuation)
        supplied_hash = body.pop("continuation_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "OOR-011 continuation hash mismatch"
            )

        lineage_values = (
            continuation.continuation_id,
            continuation.authorization_consumption_id,
            continuation.authorization_consumption_hash,
            continuation.activation_authorization_id,
            continuation.activation_authorization_hash,
            continuation.attestation_id,
            continuation.attestation_hash,
            continuation.activation_id,
            continuation.activation_hash,
            continuation.session_authorization_consumption_id,
            continuation.session_authorization_consumption_hash,
            continuation.session_authorization_id,
            continuation.session_authorization_hash,
            continuation.session_id,
            continuation.session_hash,
            continuation.admission_id,
            continuation.admission_hash,
            continuation.request_id,
            continuation.request_hash,
            continuation.dependency_receipt_id,
            continuation.dependency_receipt_hash,
            continuation.source_operator_completion_certification_id,
        )
        if not all(_valid_sha256(value) for value in lineage_values):
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "OOR-011 lineage identity invalid"
            )

        required = (
            continuation.authorization_consumption_identity_verified,
            continuation.authorization_consumption_hash_verified,
            continuation.authorization_consumption_contract_verified,
            continuation.complete_runtime_lineage_verified,
            continuation.single_consumption_scope_verified,
            continuation.single_continuation_scope_verified,
            continuation.continuation_single_use_verified,
            continuation.read_only_boundary_verified,
            continuation.deterministic_boundary_verified,
            continuation.immutable_result_boundary_verified,
            continuation.continuation_type == OOR_011_CONTINUATION_TYPE,
            continuation.continuation_status == OOR_011_CONTINUATION_STATUS,
            not continuation.duplicate_continuation_allowed,
            not continuation.continuation_reversible,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "OOR-011 continuation contract incomplete"
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
        if any(forbidden):
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "forbidden runtime capability detected"
            )

        if (
            not isinstance(attested_at, datetime)
            or attested_at.tzinfo is None
            or attested_at.utcoffset() is None
        ):
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "attested_at must be timezone-aware"
            )
        at = attested_at.astimezone(timezone.utc)
        if at < continuation.continued_at.astimezone(timezone.utc):
            raise OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError(
                "attestation cannot precede continuation"
            )

        inherited = {
            "continuation_id": continuation.continuation_id,
            "continuation_hash": continuation.continuation_hash,
            "authorization_consumption_id": continuation.authorization_consumption_id,
            "authorization_consumption_hash": continuation.authorization_consumption_hash,
            "activation_authorization_id": continuation.activation_authorization_id,
            "activation_authorization_hash": continuation.activation_authorization_hash,
            "attestation_source_id": continuation.attestation_id,
            "attestation_source_hash": continuation.attestation_hash,
            "activation_id": continuation.activation_id,
            "activation_hash": continuation.activation_hash,
            "session_authorization_consumption_id": continuation.session_authorization_consumption_id,
            "session_authorization_consumption_hash": continuation.session_authorization_consumption_hash,
            "session_authorization_id": continuation.session_authorization_id,
            "session_authorization_hash": continuation.session_authorization_hash,
            "session_id": continuation.session_id,
            "session_hash": continuation.session_hash,
            "admission_id": continuation.admission_id,
            "admission_hash": continuation.admission_hash,
            "request_id": continuation.request_id,
            "request_hash": continuation.request_hash,
            "dependency_receipt_id": continuation.dependency_receipt_id,
            "dependency_receipt_hash": continuation.dependency_receipt_hash,
            "source_operator_completion_certification_id": continuation.source_operator_completion_certification_id,
            "runtime_namespace": continuation.runtime_namespace,
            "requester_id": continuation.requester_id,
            "correlation_id": continuation.correlation_id,
            "mode": continuation.mode,
            "query_text": continuation.query_text,
            "requested_at": continuation.requested_at.astimezone(timezone.utc),
            "admitted_at": continuation.admitted_at.astimezone(timezone.utc),
            "assembled_at": continuation.assembled_at.astimezone(timezone.utc),
            "session_authorized_at": continuation.session_authorized_at.astimezone(timezone.utc),
            "session_authorization_consumed_at": continuation.session_authorization_consumed_at.astimezone(timezone.utc),
            "activated_at": continuation.activated_at.astimezone(timezone.utc),
            "activation_attested_at": continuation.attested_at.astimezone(timezone.utc),
            "activation_authorized_at": continuation.activation_authorized_at.astimezone(timezone.utc),
            "activation_authorization_consumed_at": continuation.activation_authorization_consumed_at.astimezone(timezone.utc),
            "continued_at": continuation.continued_at.astimezone(timezone.utc),
            "continuation_attested_at": at,
            "continuation_identity_verified": True,
            "continuation_hash_verified": True,
            "continuation_contract_verified": True,
            "complete_runtime_lineage_verified": True,
            "single_continuation_scope_verified": True,
            "single_attestation_scope_verified": True,
            "attestation_single_use_verified": True,
            "read_only_boundary_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_result_boundary_verified": True,
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
        inherited["attestation_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "continuation_id": continuation.continuation_id,
                "continuation_hash": continuation.continuation_hash,
                "attested_at": at,
                "attestation_type": ATTESTATION_TYPE,
            }
        )
        return OracleOperatorRuntimeSessionActivationContinuationAttestation(
            **inherited,
            attestation_hash=stable_hash(inherited),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ATTESTATION_TYPE",
    "ATTESTATION_STATUS",
    "OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError",
    "OracleOperatorRuntimeSessionActivationContinuationAttestation",
    "OracleOperatorRuntimeSessionActivationContinuationAttestationGate",
    "stable_hash",
]
