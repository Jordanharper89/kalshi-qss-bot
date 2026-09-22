from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_authorization_gate import (
    AUTHORIZATION_STATUS as OOR_005_AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE as OOR_005_AUTHORIZATION_TYPE,
    OracleOperatorRuntimeSessionAuthorization,
)

SCHEMA_VERSION = "OOR-006"
ENGINE_ID = "OOR-006"
POLICY_ID = "oracle.operator-runtime-session-authorization-consumption-gate.v1"
CONSUMPTION_TYPE = "oracle_operator_runtime_read_only_session_authorization_consumption"
CONSUMPTION_STATUS = "oracle_operator_runtime_session_authorization_consumed"


class OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(ValueError):
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
            raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
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
class OracleOperatorRuntimeSessionAuthorizationConsumption:
    consumption_id: str
    authorization_id: str
    authorization_hash: str
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
    consumed_at: datetime
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_contract_verified: bool
    single_authorization_scope_verified: bool
    single_consumption_scope_verified: bool
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
    consumption_type: str
    consumption_status: str
    consumption_hash: str


class OracleOperatorRuntimeSessionAuthorizationConsumptionGate:
    @staticmethod
    def _verify_authorization(
        authorization: OracleOperatorRuntimeSessionAuthorization,
    ) -> None:
        if not isinstance(authorization, OracleOperatorRuntimeSessionAuthorization):
            raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
                "authorization must be canonical OOR-005 runtime session authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop("authorization_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
                "OOR-005 authorization hash mismatch"
            )

        required = (
            _valid_sha256(authorization.authorization_id),
            _valid_sha256(authorization.session_id),
            _valid_sha256(authorization.session_hash),
            _valid_sha256(authorization.admission_id),
            _valid_sha256(authorization.admission_hash),
            _valid_sha256(authorization.request_id),
            _valid_sha256(authorization.request_hash),
            _valid_sha256(authorization.dependency_receipt_id),
            _valid_sha256(authorization.dependency_receipt_hash),
            _valid_sha256(authorization.source_operator_completion_certification_id),
            isinstance(authorization.runtime_namespace, str),
            bool(authorization.runtime_namespace),
            isinstance(authorization.requester_id, str),
            bool(authorization.requester_id),
            isinstance(authorization.correlation_id, str),
            bool(authorization.correlation_id),
            authorization.mode in {"query", "session", "console", "presentation"},
            isinstance(authorization.query_text, str),
            bool(authorization.query_text),
            isinstance(authorization.requested_at, datetime),
            authorization.requested_at.tzinfo is not None,
            authorization.requested_at.utcoffset() is not None,
            isinstance(authorization.admitted_at, datetime),
            authorization.admitted_at.tzinfo is not None,
            authorization.admitted_at.utcoffset() is not None,
            isinstance(authorization.assembled_at, datetime),
            authorization.assembled_at.tzinfo is not None,
            authorization.assembled_at.utcoffset() is not None,
            isinstance(authorization.authorized_at, datetime),
            authorization.authorized_at.tzinfo is not None,
            authorization.authorized_at.utcoffset() is not None,
            authorization.admitted_at.astimezone(timezone.utc)
            >= authorization.requested_at.astimezone(timezone.utc),
            authorization.assembled_at.astimezone(timezone.utc)
            >= authorization.admitted_at.astimezone(timezone.utc),
            authorization.authorized_at.astimezone(timezone.utc)
            >= authorization.assembled_at.astimezone(timezone.utc),
            authorization.session_identity_verified,
            authorization.session_hash_verified,
            authorization.session_contract_verified,
            authorization.single_session_scope_verified,
            authorization.single_authorization_scope_verified,
            authorization.read_only_boundary_verified,
            authorization.deterministic_boundary_verified,
            authorization.immutable_result_boundary_verified,
            authorization.authorization_type == OOR_005_AUTHORIZATION_TYPE,
            authorization.authorization_status == OOR_005_AUTHORIZATION_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
                "OOR-005 authorization contract is incomplete"
            )

        forbidden = (
            authorization.runtime_serving_allowed,
            authorization.network_listener_allowed,
            authorization.database_connection_allowed,
            authorization.publication_allowed,
            authorization.qseries_handoff_allowed,
            authorization.qseries_execution_allowed,
            authorization.order_creation_allowed,
            authorization.funds_movement_allowed,
            authorization.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
                "forbidden runtime capability detected"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorRuntimeSessionAuthorization,
        consumed_at: datetime,
    ) -> OracleOperatorRuntimeSessionAuthorizationConsumption:
        self._verify_authorization(authorization)
        if (
            not isinstance(consumed_at, datetime)
            or consumed_at.tzinfo is None
            or consumed_at.utcoffset() is None
        ):
            raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
                "consumed_at must be timezone-aware"
            )

        normalized_time = consumed_at.astimezone(timezone.utc)
        authorized_time = authorization.authorized_at.astimezone(timezone.utc)
        if normalized_time < authorized_time:
            raise OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError(
                "authorization consumption cannot precede authorization"
            )

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "authorization_id": authorization.authorization_id,
                "authorization_hash": authorization.authorization_hash,
                "consumed_at": normalized_time,
                "consumption_type": CONSUMPTION_TYPE,
            }
        )
        body = {
            "consumption_id": consumption_id,
            "authorization_id": authorization.authorization_id,
            "authorization_hash": authorization.authorization_hash,
            "session_id": authorization.session_id,
            "session_hash": authorization.session_hash,
            "admission_id": authorization.admission_id,
            "admission_hash": authorization.admission_hash,
            "request_id": authorization.request_id,
            "request_hash": authorization.request_hash,
            "dependency_receipt_id": authorization.dependency_receipt_id,
            "dependency_receipt_hash": authorization.dependency_receipt_hash,
            "source_operator_completion_certification_id": authorization.source_operator_completion_certification_id,
            "runtime_namespace": authorization.runtime_namespace,
            "requester_id": authorization.requester_id,
            "correlation_id": authorization.correlation_id,
            "mode": authorization.mode,
            "query_text": authorization.query_text,
            "requested_at": authorization.requested_at.astimezone(timezone.utc),
            "admitted_at": authorization.admitted_at.astimezone(timezone.utc),
            "assembled_at": authorization.assembled_at.astimezone(timezone.utc),
            "authorized_at": authorized_time,
            "consumed_at": normalized_time,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_contract_verified": True,
            "single_authorization_scope_verified": True,
            "single_consumption_scope_verified": True,
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
            "consumption_type": CONSUMPTION_TYPE,
            "consumption_status": CONSUMPTION_STATUS,
        }
        return OracleOperatorRuntimeSessionAuthorizationConsumption(
            **body,
            consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_TYPE",
    "CONSUMPTION_STATUS",
    "OracleOperatorRuntimeSessionAuthorizationConsumption",
    "OracleOperatorRuntimeSessionAuthorizationConsumptionGate",
    "OracleOperatorRuntimeSessionAuthorizationConsumptionInvariantError",
    "stable_hash",
]
