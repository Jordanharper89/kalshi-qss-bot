from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_admission_gate import (
    ADMISSION_STATUS as OOR_003_ADMISSION_STATUS,
    ADMISSION_TYPE as OOR_003_ADMISSION_TYPE,
    OracleOperatorRuntimeRequestAdmission,
)

SCHEMA_VERSION = "OOR-004"
ENGINE_ID = "OOR-004"
POLICY_ID = "oracle.operator-runtime-session-assembly-gate.v1"
SESSION_TYPE = "oracle_operator_runtime_read_only_session"
SESSION_STATUS = "oracle_operator_runtime_session_assembled"


class OracleOperatorRuntimeSessionAssemblyInvariantError(ValueError):
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
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionAssemblyInvariantError(
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
class OracleOperatorRuntimeSession:
    session_id: str
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
    request_identity_verified: bool
    admission_identity_verified: bool
    admission_hash_verified: bool
    admission_contract_verified: bool
    single_request_scope_verified: bool
    single_session_scope_verified: bool
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
    session_type: str
    session_status: str
    session_hash: str


class OracleOperatorRuntimeSessionAssemblyGate:
    @staticmethod
    def _verify_admission(admission: OracleOperatorRuntimeRequestAdmission) -> None:
        if not isinstance(admission, OracleOperatorRuntimeRequestAdmission):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "admission must be canonical OOR-003 request admission"
            )

        body = asdict(admission)
        supplied_hash = body.pop("admission_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "OOR-003 admission hash mismatch"
            )

        required = (
            _valid_sha256(admission.admission_id),
            _valid_sha256(admission.request_id),
            _valid_sha256(admission.request_hash),
            _valid_sha256(admission.dependency_receipt_id),
            _valid_sha256(admission.dependency_receipt_hash),
            _valid_sha256(admission.source_operator_completion_certification_id),
            isinstance(admission.runtime_namespace, str),
            bool(admission.runtime_namespace),
            isinstance(admission.requester_id, str),
            bool(admission.requester_id),
            isinstance(admission.correlation_id, str),
            bool(admission.correlation_id),
            admission.mode in {"query", "session", "console", "presentation"},
            isinstance(admission.query_text, str),
            bool(admission.query_text),
            isinstance(admission.requested_at, datetime),
            admission.requested_at.tzinfo is not None,
            admission.requested_at.utcoffset() is not None,
            isinstance(admission.admitted_at, datetime),
            admission.admitted_at.tzinfo is not None,
            admission.admitted_at.utcoffset() is not None,
            admission.admitted_at.astimezone(timezone.utc)
            >= admission.requested_at.astimezone(timezone.utc),
            admission.request_identity_verified,
            admission.request_hash_verified,
            admission.request_contract_verified,
            admission.request_mode_verified,
            admission.request_text_verified,
            admission.read_only_boundary_verified,
            admission.deterministic_boundary_verified,
            admission.immutable_result_boundary_verified,
            admission.admission_type == OOR_003_ADMISSION_TYPE,
            admission.admission_status == OOR_003_ADMISSION_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "OOR-003 admission contract is incomplete"
            )

        forbidden = (
            admission.runtime_serving_allowed,
            admission.network_listener_allowed,
            admission.database_connection_allowed,
            admission.publication_allowed,
            admission.qseries_handoff_allowed,
            admission.qseries_execution_allowed,
            admission.order_creation_allowed,
            admission.funds_movement_allowed,
            admission.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "forbidden runtime capability detected"
            )

    def assemble(
        self,
        *,
        admission: OracleOperatorRuntimeRequestAdmission,
        assembled_at: datetime,
    ) -> OracleOperatorRuntimeSession:
        self._verify_admission(admission)
        if (
            not isinstance(assembled_at, datetime)
            or assembled_at.tzinfo is None
            or assembled_at.utcoffset() is None
        ):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "assembled_at must be timezone-aware"
            )

        normalized_time = assembled_at.astimezone(timezone.utc)
        admitted_time = admission.admitted_at.astimezone(timezone.utc)
        if normalized_time < admitted_time:
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "session assembly cannot precede admission"
            )

        session_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "admission_id": admission.admission_id,
                "admission_hash": admission.admission_hash,
                "assembled_at": normalized_time,
                "session_type": SESSION_TYPE,
            }
        )
        body = {
            "session_id": session_id,
            "admission_id": admission.admission_id,
            "admission_hash": admission.admission_hash,
            "request_id": admission.request_id,
            "request_hash": admission.request_hash,
            "dependency_receipt_id": admission.dependency_receipt_id,
            "dependency_receipt_hash": admission.dependency_receipt_hash,
            "source_operator_completion_certification_id": admission.source_operator_completion_certification_id,
            "runtime_namespace": admission.runtime_namespace,
            "requester_id": admission.requester_id,
            "correlation_id": admission.correlation_id,
            "mode": admission.mode,
            "query_text": admission.query_text,
            "requested_at": admission.requested_at.astimezone(timezone.utc),
            "admitted_at": admitted_time,
            "assembled_at": normalized_time,
            "request_identity_verified": True,
            "admission_identity_verified": True,
            "admission_hash_verified": True,
            "admission_contract_verified": True,
            "single_request_scope_verified": True,
            "single_session_scope_verified": True,
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
            "session_type": SESSION_TYPE,
            "session_status": SESSION_STATUS,
        }
        return OracleOperatorRuntimeSession(
            **body,
            session_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "SESSION_TYPE",
    "SESSION_STATUS",
    "OracleOperatorRuntimeSession",
    "OracleOperatorRuntimeSessionAssemblyGate",
    "OracleOperatorRuntimeSessionAssemblyInvariantError",
    "stable_hash",
]
