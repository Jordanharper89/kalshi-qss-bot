from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_assembly_gate import (
    SESSION_STATUS as OOR_004_SESSION_STATUS,
    SESSION_TYPE as OOR_004_SESSION_TYPE,
    OracleOperatorRuntimeSession,
)

SCHEMA_VERSION = "OOR-005"
ENGINE_ID = "OOR-005"
POLICY_ID = "oracle.operator-runtime-session-authorization-gate.v1"
AUTHORIZATION_TYPE = "oracle_operator_runtime_read_only_session_authorization"
AUTHORIZATION_STATUS = "oracle_operator_runtime_session_authorized"


class OracleOperatorRuntimeSessionAuthorizationInvariantError(ValueError):
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
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleOperatorRuntimeSessionAuthorization:
    authorization_id: str
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
    authorized_at: datetime
    session_identity_verified: bool
    session_hash_verified: bool
    session_contract_verified: bool
    single_session_scope_verified: bool
    single_authorization_scope_verified: bool
    read_only_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_result_boundary_verified: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    authorization_type: str
    authorization_status: str
    authorization_hash: str


class OracleOperatorRuntimeSessionAuthorizationGate:
    @staticmethod
    def _verify_session(session: OracleOperatorRuntimeSession) -> None:
        if not isinstance(session, OracleOperatorRuntimeSession):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "session must be canonical OOR-004 runtime session"
            )

        body = asdict(session)
        supplied_hash = body.pop("session_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "OOR-004 session hash mismatch"
            )

        required = (
            _valid_sha256(session.session_id),
            _valid_sha256(session.admission_id),
            _valid_sha256(session.admission_hash),
            _valid_sha256(session.request_id),
            _valid_sha256(session.request_hash),
            _valid_sha256(session.dependency_receipt_id),
            _valid_sha256(session.dependency_receipt_hash),
            _valid_sha256(session.source_operator_completion_certification_id),
            isinstance(session.runtime_namespace, str),
            bool(session.runtime_namespace),
            isinstance(session.requester_id, str),
            bool(session.requester_id),
            isinstance(session.correlation_id, str),
            bool(session.correlation_id),
            session.mode in {"query", "session", "console", "presentation"},
            isinstance(session.query_text, str),
            bool(session.query_text),
            isinstance(session.requested_at, datetime),
            session.requested_at.tzinfo is not None,
            session.requested_at.utcoffset() is not None,
            isinstance(session.admitted_at, datetime),
            session.admitted_at.tzinfo is not None,
            session.admitted_at.utcoffset() is not None,
            isinstance(session.assembled_at, datetime),
            session.assembled_at.tzinfo is not None,
            session.assembled_at.utcoffset() is not None,
            session.admitted_at.astimezone(timezone.utc)
            >= session.requested_at.astimezone(timezone.utc),
            session.assembled_at.astimezone(timezone.utc)
            >= session.admitted_at.astimezone(timezone.utc),
            session.request_identity_verified,
            session.admission_identity_verified,
            session.admission_hash_verified,
            session.admission_contract_verified,
            session.single_request_scope_verified,
            session.single_session_scope_verified,
            session.read_only_boundary_verified,
            session.deterministic_boundary_verified,
            session.immutable_result_boundary_verified,
            session.session_type == OOR_004_SESSION_TYPE,
            session.session_status == OOR_004_SESSION_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "OOR-004 session contract is incomplete"
            )

        forbidden = (
            session.runtime_serving_allowed,
            session.network_listener_allowed,
            session.database_connection_allowed,
            session.publication_allowed,
            session.qseries_handoff_allowed,
            session.qseries_execution_allowed,
            session.order_creation_allowed,
            session.funds_movement_allowed,
            session.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "forbidden runtime capability detected"
            )

    def authorize(
        self,
        *,
        session: OracleOperatorRuntimeSession,
        authorized_at: datetime,
    ) -> OracleOperatorRuntimeSessionAuthorization:
        self._verify_session(session)
        if (
            not isinstance(authorized_at, datetime)
            or authorized_at.tzinfo is None
            or authorized_at.utcoffset() is None
        ):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "authorized_at must be timezone-aware"
            )

        normalized_time = authorized_at.astimezone(timezone.utc)
        assembled_time = session.assembled_at.astimezone(timezone.utc)
        if normalized_time < assembled_time:
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "session authorization cannot precede assembly"
            )

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "session_id": session.session_id,
                "session_hash": session.session_hash,
                "authorized_at": normalized_time,
                "authorization_type": AUTHORIZATION_TYPE,
            }
        )
        body = {
            "authorization_id": authorization_id,
            "session_id": session.session_id,
            "session_hash": session.session_hash,
            "admission_id": session.admission_id,
            "admission_hash": session.admission_hash,
            "request_id": session.request_id,
            "request_hash": session.request_hash,
            "dependency_receipt_id": session.dependency_receipt_id,
            "dependency_receipt_hash": session.dependency_receipt_hash,
            "source_operator_completion_certification_id": session.source_operator_completion_certification_id,
            "runtime_namespace": session.runtime_namespace,
            "requester_id": session.requester_id,
            "correlation_id": session.correlation_id,
            "mode": session.mode,
            "query_text": session.query_text,
            "requested_at": session.requested_at.astimezone(timezone.utc),
            "admitted_at": session.admitted_at.astimezone(timezone.utc),
            "assembled_at": assembled_time,
            "authorized_at": normalized_time,
            "session_identity_verified": True,
            "session_hash_verified": True,
            "session_contract_verified": True,
            "single_session_scope_verified": True,
            "single_authorization_scope_verified": True,
            "read_only_boundary_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_result_boundary_verified": True,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "authorization_type": AUTHORIZATION_TYPE,
            "authorization_status": AUTHORIZATION_STATUS,
        }
        return OracleOperatorRuntimeSessionAuthorization(
            **body,
            authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_TYPE",
    "AUTHORIZATION_STATUS",
    "OracleOperatorRuntimeSessionAuthorization",
    "OracleOperatorRuntimeSessionAuthorizationGate",
    "OracleOperatorRuntimeSessionAuthorizationInvariantError",
    "stable_hash",
]
