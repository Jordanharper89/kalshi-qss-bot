from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_request_contract import (
    ALLOWED_RESPONSE_MODES,
    REQUEST_STATUS as ORR_002_REQUEST_STATUS,
    REQUEST_TYPE as ORR_002_REQUEST_TYPE,
    SUBSYSTEM_NAMESPACE,
    OracleResearchResponseRequest,
)

SCHEMA_VERSION = "ORR-003"
ENGINE_ID = "ORR-003"
POLICY_ID = "oracle.research-response.request-admission-gate.v1"
ADMISSION_TYPE = "oracle_research_response_request_admission"
ADMISSION_STATUS = "oracle_research_response_request_admitted"


class OracleResearchResponseRequestAdmissionInvariantError(ValueError):
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
            raise OracleResearchResponseRequestAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseRequestAdmissionInvariantError(
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
class OracleResearchResponseRequestAdmission:
    admission_id: str
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
    request_identity_verified: bool
    request_hash_verified: bool
    request_contract_verified: bool
    typed_question_verified: bool
    response_mode_verified: bool
    filter_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_admission_boundary_verified: bool
    read_only_boundary_verified: bool
    single_request_scope_verified: bool
    admission_single_use_verified: bool
    duplicate_admission_allowed: bool
    admission_reversible: bool
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


class OracleResearchResponseRequestAdmissionGate:
    def admit(
        self,
        *,
        request: OracleResearchResponseRequest,
        admitted_at: datetime,
    ) -> OracleResearchResponseRequestAdmission:
        if not isinstance(request, OracleResearchResponseRequest):
            raise OracleResearchResponseRequestAdmissionInvariantError(
                "request must be canonical ORR-002 request"
            )

        request_body = asdict(request)
        supplied_hash = request_body.pop("request_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(request_body) != supplied_hash:
            raise OracleResearchResponseRequestAdmissionInvariantError(
                "ORR-002 request hash mismatch"
            )

        required = (
            _valid_sha256(request.request_id),
            _valid_sha256(request.dependency_receipt_id),
            _valid_sha256(request.dependency_receipt_hash),
            _valid_sha256(request.source_runtime_completion_id),
            _valid_sha256(request.source_runtime_completion_hash),
            request.subsystem_namespace == SUBSYSTEM_NAMESPACE,
            request.response_mode in ALLOWED_RESPONSE_MODES,
            request.request_type == ORR_002_REQUEST_TYPE,
            request.request_status == ORR_002_REQUEST_STATUS,
            request.dependency_identity_verified,
            request.dependency_hash_verified,
            request.dependency_contract_verified,
            request.typed_question_verified,
            request.response_mode_verified,
            request.filter_boundary_verified,
            request.deterministic_boundary_verified,
            request.immutable_request_boundary_verified,
            request.read_only_boundary_verified,
            request.request_single_use_verified,
            not request.duplicate_request_allowed,
            not request.request_reversible,
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
        if not all(required) or any(forbidden):
            raise OracleResearchResponseRequestAdmissionInvariantError(
                "ORR-002 request contract incomplete or unsafe"
            )

        if not request.question_text.strip():
            raise OracleResearchResponseRequestAdmissionInvariantError(
                "question_text cannot be empty"
            )

        if (
            not isinstance(admitted_at, datetime)
            or admitted_at.tzinfo is None
            or admitted_at.utcoffset() is None
        ):
            raise OracleResearchResponseRequestAdmissionInvariantError(
                "admitted_at must be timezone-aware"
            )
        at = admitted_at.astimezone(timezone.utc)
        if at < request.requested_at.astimezone(timezone.utc):
            raise OracleResearchResponseRequestAdmissionInvariantError(
                "admission cannot precede request"
            )

        body = {
            "request_id": request.request_id,
            "request_hash": request.request_hash,
            "dependency_receipt_id": request.dependency_receipt_id,
            "dependency_receipt_hash": request.dependency_receipt_hash,
            "source_runtime_completion_id": request.source_runtime_completion_id,
            "source_runtime_completion_hash": request.source_runtime_completion_hash,
            "subsystem_namespace": request.subsystem_namespace,
            "requester_id": request.requester_id,
            "correlation_id": request.correlation_id,
            "question_text": request.question_text,
            "response_mode": request.response_mode,
            "filters": request.filters,
            "requested_at": request.requested_at.astimezone(timezone.utc),
            "admitted_at": at,
            "request_identity_verified": True,
            "request_hash_verified": True,
            "request_contract_verified": True,
            "typed_question_verified": True,
            "response_mode_verified": True,
            "filter_boundary_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_admission_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_request_scope_verified": True,
            "admission_single_use_verified": True,
            "duplicate_admission_allowed": False,
            "admission_reversible": False,
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
        body["admission_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "request_id": request.request_id,
                "request_hash": request.request_hash,
                "admitted_at": at,
                "admission_type": ADMISSION_TYPE,
            }
        )
        return OracleResearchResponseRequestAdmission(
            **body,
            admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ADMISSION_TYPE",
    "ADMISSION_STATUS",
    "OracleResearchResponseRequestAdmissionInvariantError",
    "OracleResearchResponseRequestAdmission",
    "OracleResearchResponseRequestAdmissionGate",
    "stable_hash",
]
