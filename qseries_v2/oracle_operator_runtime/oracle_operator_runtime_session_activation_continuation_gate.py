from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOR_010_CONSUMPTION_STATUS,
    CONSUMPTION_TYPE as OOR_010_CONSUMPTION_TYPE,
    OracleOperatorRuntimeSessionActivationAuthorizationConsumption,
)

SCHEMA_VERSION = "OOR-011"
ENGINE_ID = "OOR-011"
POLICY_ID = "oracle.operator-runtime-session-activation-continuation-gate.v1"
CONTINUATION_TYPE = "oracle_operator_runtime_read_only_session_activation_continuation"
CONTINUATION_STATUS = "oracle_operator_runtime_session_activation_continued"

class OracleOperatorRuntimeSessionActivationContinuationInvariantError(ValueError):
    pass

def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionActivationContinuationInvariantError(f"unsupported value type: {type(value)!r}")

def stable_hash(value: Any) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)

@dataclass(frozen=True)
class OracleOperatorRuntimeSessionActivationContinuation:
    continuation_id: str
    authorization_consumption_id: str
    authorization_consumption_hash: str
    activation_authorization_id: str
    activation_authorization_hash: str
    attestation_id: str
    attestation_hash: str
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
    attested_at: datetime
    activation_authorized_at: datetime
    activation_authorization_consumed_at: datetime
    continued_at: datetime
    authorization_consumption_identity_verified: bool
    authorization_consumption_hash_verified: bool
    authorization_consumption_contract_verified: bool
    complete_runtime_lineage_verified: bool
    single_consumption_scope_verified: bool
    single_continuation_scope_verified: bool
    continuation_single_use_verified: bool
    read_only_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_result_boundary_verified: bool
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

class OracleOperatorRuntimeSessionActivationContinuationGate:
    def continue_session_activation(
        self,
        *,
        consumption: OracleOperatorRuntimeSessionActivationAuthorizationConsumption,
        continued_at: datetime,
    ) -> OracleOperatorRuntimeSessionActivationContinuation:
        if not isinstance(consumption, OracleOperatorRuntimeSessionActivationAuthorizationConsumption):
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError(
                "consumption must be canonical OOR-010 authorization consumption"
            )
        body = asdict(consumption)
        supplied = body.pop("consumption_hash", None)
        if not _sha(supplied) or stable_hash(body) != supplied:
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError("OOR-010 consumption hash mismatch")
        ids = (
            consumption.consumption_id,
            consumption.activation_authorization_id,
            consumption.activation_authorization_hash,
            consumption.attestation_id,
            consumption.attestation_hash,
            consumption.activation_id,
            consumption.activation_hash,
            consumption.session_authorization_consumption_id,
            consumption.session_authorization_consumption_hash,
            consumption.session_authorization_id,
            consumption.session_authorization_hash,
            consumption.session_id,
            consumption.session_hash,
            consumption.admission_id,
            consumption.admission_hash,
            consumption.request_id,
            consumption.request_hash,
            consumption.dependency_receipt_id,
            consumption.dependency_receipt_hash,
            consumption.source_operator_completion_certification_id,
        )
        if not all(_sha(value) for value in ids):
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError("OOR-010 lineage identity invalid")
        required = (
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_contract_verified,
            consumption.complete_runtime_lineage_verified,
            consumption.single_authorization_scope_verified,
            consumption.single_consumption_scope_verified,
            consumption.read_only_boundary_verified,
            consumption.deterministic_boundary_verified,
            consumption.immutable_result_boundary_verified,
            consumption.consumption_type == OOR_010_CONSUMPTION_TYPE,
            consumption.consumption_status == OOR_010_CONSUMPTION_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError("OOR-010 consumption contract incomplete")
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
        if any(forbidden):
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError("forbidden runtime capability detected")
        if not isinstance(continued_at, datetime) or continued_at.tzinfo is None or continued_at.utcoffset() is None:
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError("continued_at must be timezone-aware")
        at = continued_at.astimezone(timezone.utc)
        if at < consumption.activation_authorization_consumed_at.astimezone(timezone.utc):
            raise OracleOperatorRuntimeSessionActivationContinuationInvariantError(
                "continuation cannot precede activation authorization consumption"
            )
        inherited = {
            "authorization_consumption_id": consumption.consumption_id,
            "authorization_consumption_hash": consumption.consumption_hash,
            "activation_authorization_id": consumption.activation_authorization_id,
            "activation_authorization_hash": consumption.activation_authorization_hash,
            "attestation_id": consumption.attestation_id,
            "attestation_hash": consumption.attestation_hash,
            "activation_id": consumption.activation_id,
            "activation_hash": consumption.activation_hash,
            "session_authorization_consumption_id": consumption.session_authorization_consumption_id,
            "session_authorization_consumption_hash": consumption.session_authorization_consumption_hash,
            "session_authorization_id": consumption.session_authorization_id,
            "session_authorization_hash": consumption.session_authorization_hash,
            "session_id": consumption.session_id,
            "session_hash": consumption.session_hash,
            "admission_id": consumption.admission_id,
            "admission_hash": consumption.admission_hash,
            "request_id": consumption.request_id,
            "request_hash": consumption.request_hash,
            "dependency_receipt_id": consumption.dependency_receipt_id,
            "dependency_receipt_hash": consumption.dependency_receipt_hash,
            "source_operator_completion_certification_id": consumption.source_operator_completion_certification_id,
            "runtime_namespace": consumption.runtime_namespace,
            "requester_id": consumption.requester_id,
            "correlation_id": consumption.correlation_id,
            "mode": consumption.mode,
            "query_text": consumption.query_text,
            "requested_at": consumption.requested_at.astimezone(timezone.utc),
            "admitted_at": consumption.admitted_at.astimezone(timezone.utc),
            "assembled_at": consumption.assembled_at.astimezone(timezone.utc),
            "session_authorized_at": consumption.session_authorized_at.astimezone(timezone.utc),
            "session_authorization_consumed_at": consumption.session_authorization_consumed_at.astimezone(timezone.utc),
            "activated_at": consumption.activated_at.astimezone(timezone.utc),
            "attested_at": consumption.attested_at.astimezone(timezone.utc),
            "activation_authorized_at": consumption.activation_authorized_at.astimezone(timezone.utc),
            "activation_authorization_consumed_at": consumption.activation_authorization_consumed_at.astimezone(timezone.utc),
            "continued_at": at,
            "authorization_consumption_identity_verified": True,
            "authorization_consumption_hash_verified": True,
            "authorization_consumption_contract_verified": True,
            "complete_runtime_lineage_verified": True,
            "single_consumption_scope_verified": True,
            "single_continuation_scope_verified": True,
            "continuation_single_use_verified": True,
            "read_only_boundary_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_result_boundary_verified": True,
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
        inherited["continuation_id"] = stable_hash({
            "engine_id": ENGINE_ID,
            "authorization_consumption_id": consumption.consumption_id,
            "authorization_consumption_hash": consumption.consumption_hash,
            "continued_at": at,
            "continuation_type": CONTINUATION_TYPE,
        })
        return OracleOperatorRuntimeSessionActivationContinuation(
            **inherited,
            continuation_hash=stable_hash(inherited),
        )

__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONTINUATION_TYPE",
    "CONTINUATION_STATUS",
    "OracleOperatorRuntimeSessionActivationContinuationInvariantError",
    "OracleOperatorRuntimeSessionActivationContinuation",
    "OracleOperatorRuntimeSessionActivationContinuationGate",
    "stable_hash",
]
