from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_contract import (
    REQUEST_STATUS as OOR_002_REQUEST_STATUS,
    REQUEST_TYPE as OOR_002_REQUEST_TYPE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeRequest,
)

SCHEMA_VERSION = "OOR-003"
ENGINE_ID = "OOR-003"
POLICY_ID = "oracle.operator-runtime-request-admission-gate.v1"
ADMISSION_TYPE = "oracle_operator_runtime_read_only_request_admission"
ADMISSION_STATUS = "oracle_operator_runtime_request_admitted"

_ALLOWED_MODES = frozenset({"query", "session", "console", "presentation"})


class OracleOperatorRuntimeRequestAdmissionInvariantError(ValueError):
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
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeRequestAdmissionInvariantError(
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
class OracleOperatorRuntimeRequestAdmission:
    admission_id: str
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
    request_identity_verified: bool
    request_hash_verified: bool
    request_contract_verified: bool
    request_mode_verified: bool
    request_text_verified: bool
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
    admission_type: str
    admission_status: str
    admission_hash: str


class OracleOperatorRuntimeRequestAdmissionGate:
    @staticmethod
    def _verify_request(request: OracleOperatorRuntimeRequest) -> None:
        if not isinstance(request, OracleOperatorRuntimeRequest):
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "request must be canonical OOR-002 runtime request"
            )

        body = asdict(request)
        supplied_hash = body.pop("request_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "OOR-002 request hash mismatch"
            )

        required = (
            _valid_sha256(request.request_id),
            _valid_sha256(request.dependency_receipt_id),
            _valid_sha256(request.dependency_receipt_hash),
            _valid_sha256(request.source_operator_completion_certification_id),
            request.runtime_namespace == RUNTIME_NAMESPACE,
            request.mode in _ALLOWED_MODES,
            isinstance(request.query_text, str),
            bool(request.query_text),
            request.query_text == " ".join(request.query_text.split()),
            isinstance(request.requested_at, datetime),
            request.requested_at.tzinfo is not None,
            request.requested_at.utcoffset() is not None,
            request.read_only_required,
            request.deterministic_required,
            request.immutable_result_required,
            request.request_type == OOR_002_REQUEST_TYPE,
            request.request_status == OOR_002_REQUEST_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "OOR-002 request contract is incomplete"
            )

        forbidden = (
            request.runtime_serving_allowed,
            request.network_listener_allowed,
            request.database_connection_allowed,
            request.publication_allowed,
            request.qseries_handoff_allowed,
            request.qseries_execution_allowed,
            request.order_creation_allowed,
            request.funds_movement_allowed,
            request.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "forbidden runtime request capability detected"
            )

    def admit(
        self,
        *,
        request: OracleOperatorRuntimeRequest,
        admitted_at: datetime,
    ) -> OracleOperatorRuntimeRequestAdmission:
        self._verify_request(request)
        if not isinstance(admitted_at, datetime) or admitted_at.tzinfo is None or admitted_at.utcoffset() is None:
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "admitted_at must be timezone-aware"
            )
        normalized_time = admitted_at.astimezone(timezone.utc)
        requested_time = request.requested_at.astimezone(timezone.utc)
        if normalized_time < requested_time:
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "admission cannot precede request"
            )

        admission_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "request_id": request.request_id,
                "request_hash": request.request_hash,
                "admitted_at": normalized_time,
                "admission_type": ADMISSION_TYPE,
            }
        )
        body = {
            "admission_id": admission_id,
            "request_id": request.request_id,
            "request_hash": request.request_hash,
            "dependency_receipt_id": request.dependency_receipt_id,
            "dependency_receipt_hash": request.dependency_receipt_hash,
            "source_operator_completion_certification_id": request.source_operator_completion_certification_id,
            "runtime_namespace": request.runtime_namespace,
            "requester_id": request.requester_id,
            "correlation_id": request.correlation_id,
            "mode": request.mode,
            "query_text": request.query_text,
            "requested_at": requested_time,
            "admitted_at": normalized_time,
            "request_identity_verified": True,
            "request_hash_verified": True,
            "request_contract_verified": True,
            "request_mode_verified": True,
            "request_text_verified": True,
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
            "admission_type": ADMISSION_TYPE,
            "admission_status": ADMISSION_STATUS,
        }
        return OracleOperatorRuntimeRequestAdmission(
            **body,
            admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ADMISSION_TYPE",
    "ADMISSION_STATUS",
    "OracleOperatorRuntimeRequestAdmission",
    "OracleOperatorRuntimeRequestAdmissionGate",
    "OracleOperatorRuntimeRequestAdmissionInvariantError",
    "stable_hash",
]
