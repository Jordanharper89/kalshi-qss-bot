from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_request_contract import (
    EXPECTED_CONSUMER_ID,
    EXPECTED_PROJECTION,
    QUERY_REQUEST_STATUS as OOP_003_QUERY_REQUEST_STATUS,
    OracleOperatorQueryRequest,
)

SCHEMA_VERSION = "OOP-004"
ENGINE_ID = "OOP-004"
POLICY_ID = "oracle.operator.query-request-admission-gate.v1"
ADMISSION_SCHEMA_VERSION = "oracle.operator.query.request-admission.v1"
ADMISSION_STATUS = "operator_query_request_admitted"
EXPECTED_QUERY_REQUEST_STATUS = OOP_003_QUERY_REQUEST_STATUS
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryRequestAdmissionInvariantError(RuntimeError):
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
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryRequestAdmissionInvariantError(
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
class OracleOperatorQueryRequestAdmission:
    query_admission_id: str
    source_query_request_id: str
    source_query_request_hash: str
    source_admission_id: str
    source_admission_hash: str
    source_dependency_receipt_id: str
    source_dependency_receipt_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    operator_namespace: str
    query_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    admitted_entry_count: int
    admitted_response_artifact_entry_ids: tuple[str, ...]
    admitted_query_response_ids: tuple[str, ...]
    query_request_type_verified: bool
    query_request_identity_verified: bool
    query_request_hash_verified: bool
    query_request_status_verified: bool
    source_admission_lineage_verified: bool
    source_dependency_lineage_verified: bool
    source_authorization_lineage_verified: bool
    operator_namespace_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    query_parameters_verified: bool
    authorized_scope_verified: bool
    authorized_scope_frozen: bool
    deterministic_admission_verified: bool
    analytics_read_only_dependency_preserved: bool
    query_resolution_allowed: bool
    query_resolution_performed: bool
    analytics_query_execution_allowed: bool
    analytics_query_execution_performed: bool
    analytics_reexecution_allowed: bool
    analytics_reexecution_performed: bool
    analytics_database_connection_allowed: bool
    analytics_database_connection_performed: bool
    analytics_mutation_allowed: bool
    analytics_mutation_performed: bool
    operator_session_construction_allowed: bool
    operator_console_rendering_allowed: bool
    operator_presentation_rendering_allowed: bool
    publication_allowed: bool
    publication_performed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    admission_status: str
    query_admission_hash: str


class OracleOperatorQueryRequestAdmissionGate:
    @staticmethod
    def _verify_request(request: OracleOperatorQueryRequest) -> None:
        if not isinstance(request, OracleOperatorQueryRequest):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "source must be the canonical OOP-003 query request"
            )

        body = asdict(request)
        supplied_hash = body.pop("query_request_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 query request hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 query request hash mismatch"
            )

        required_hashes = (
            request.query_request_id,
            request.source_admission_hash,
            request.source_dependency_receipt_hash,
            request.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 request lineage contains invalid hashes"
            )
        if request.query_request_status != EXPECTED_QUERY_REQUEST_STATUS:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 query request is not materialized"
            )
        if request.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "operator namespace mismatch"
            )
        if request.consumer_id != EXPECTED_CONSUMER_ID:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "consumer identity mismatch"
            )
        if request.projection != EXPECTED_PROJECTION:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "projection identity mismatch"
            )

        if request.authorized_entry_count < 1:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "query request contains no authorized entries"
            )
        if request.authorized_entry_count != len(
            request.authorized_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if request.authorized_entry_count != len(
            request.authorized_query_response_ids
        ):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(request.authorized_response_artifact_entry_ids)) != request.authorized_entry_count:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(request.authorized_query_response_ids)) != request.authorized_entry_count:
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            request.admission_type_verified,
            request.admission_hash_verified,
            request.admission_status_verified,
            request.consumer_identity_verified,
            request.projection_identity_verified,
            request.query_mode_verified,
            request.time_scope_verified,
            request.sort_order_verified,
            request.result_limit_verified,
            request.authorized_scope_preserved,
            request.deterministic_request_verified,
            request.analytics_read_only_dependency_preserved,
        )
        if not all(required_truths):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 request is incomplete"
            )

        forbidden_authority = (
            request.analytics_query_execution_allowed,
            request.analytics_query_execution_performed,
            request.analytics_reexecution_allowed,
            request.analytics_reexecution_performed,
            request.analytics_database_connection_allowed,
            request.analytics_database_connection_performed,
            request.analytics_mutation_allowed,
            request.analytics_mutation_performed,
            request.operator_session_construction_allowed,
            request.operator_console_rendering_allowed,
            request.operator_presentation_rendering_allowed,
            request.publication_allowed,
            request.publication_performed,
            request.qseries_handoff_allowed,
            request.qseries_execution_allowed,
            request.qseries_execution_performed,
            request.order_creation_allowed,
            request.order_creation_performed,
            request.funds_movement_allowed,
            request.funds_movement_performed,
            request.portfolio_mutation_allowed,
            request.portfolio_mutation_performed,
        )
        if any(forbidden_authority):
            raise OracleOperatorQueryRequestAdmissionInvariantError(
                "OOP-003 request contains forbidden authority or activity"
            )

    def admit(self, *, request: OracleOperatorQueryRequest) -> OracleOperatorQueryRequestAdmission:
        self._verify_request(request)

        query_admission_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_query_request_id": request.query_request_id,
                "source_query_request_hash": request.query_request_hash,
                "query_mode": request.query_mode,
                "query_text": request.query_text,
                "time_scope": request.time_scope,
                "sort_order": request.sort_order,
                "result_limit": request.result_limit,
                "requested_tags": request.requested_tags,
                "authorized_response_artifact_entry_ids": request.authorized_response_artifact_entry_ids,
                "authorized_query_response_ids": request.authorized_query_response_ids,
            }
        )

        body = {
            "query_admission_id": query_admission_id,
            "source_query_request_id": request.query_request_id,
            "source_query_request_hash": request.query_request_hash,
            "source_admission_id": request.source_admission_id,
            "source_admission_hash": request.source_admission_hash,
            "source_dependency_receipt_id": request.source_dependency_receipt_id,
            "source_dependency_receipt_hash": request.source_dependency_receipt_hash,
            "source_authorization_id": request.source_authorization_id,
            "source_authorization_hash": request.source_authorization_hash,
            "operator_namespace": request.operator_namespace,
            "query_namespace": EXPECTED_QUERY_NAMESPACE,
            "consumer_id": request.consumer_id,
            "projection": request.projection,
            "query_mode": request.query_mode,
            "query_text": request.query_text,
            "time_scope": request.time_scope,
            "sort_order": request.sort_order,
            "result_limit": request.result_limit,
            "requested_tags": tuple(request.requested_tags),
            "admitted_entry_count": request.authorized_entry_count,
            "admitted_response_artifact_entry_ids": tuple(request.authorized_response_artifact_entry_ids),
            "admitted_query_response_ids": tuple(request.authorized_query_response_ids),
            "query_request_type_verified": True,
            "query_request_identity_verified": True,
            "query_request_hash_verified": True,
            "query_request_status_verified": True,
            "source_admission_lineage_verified": True,
            "source_dependency_lineage_verified": True,
            "source_authorization_lineage_verified": True,
            "operator_namespace_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "query_parameters_verified": True,
            "authorized_scope_verified": True,
            "authorized_scope_frozen": True,
            "deterministic_admission_verified": True,
            "analytics_read_only_dependency_preserved": True,
            "query_resolution_allowed": True,
            "query_resolution_performed": False,
            "analytics_query_execution_allowed": False,
            "analytics_query_execution_performed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_allowed": False,
            "analytics_database_connection_performed": False,
            "analytics_mutation_allowed": False,
            "analytics_mutation_performed": False,
            "operator_session_construction_allowed": False,
            "operator_console_rendering_allowed": False,
            "operator_presentation_rendering_allowed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "admission_status": ADMISSION_STATUS,
        }
        return OracleOperatorQueryRequestAdmission(
            **body,
            query_admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ADMISSION_SCHEMA_VERSION",
    "ADMISSION_STATUS",
    "EXPECTED_QUERY_REQUEST_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryRequestAdmission",
    "OracleOperatorQueryRequestAdmissionGate",
    "OracleOperatorQueryRequestAdmissionInvariantError",
    "stable_hash",
]
