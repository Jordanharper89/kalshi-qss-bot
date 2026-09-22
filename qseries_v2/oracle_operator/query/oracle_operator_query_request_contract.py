from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_operator.oracle_operator_analytics_dependency_admission_gate import (
    ADMISSION_STATUS as OOP_002_ADMISSION_STATUS,
    EXPECTED_OPERATOR_NAMESPACE,
    OracleOperatorAnalyticsDependencyAdmission,
)

SCHEMA_VERSION = "OOP-003"
ENGINE_ID = "OOP-003"
POLICY_ID = "oracle.operator.query-request-contract.v1"
QUERY_REQUEST_SCHEMA_VERSION = "oracle.operator.query.request.v1"
QUERY_REQUEST_STATUS = "operator_query_request_materialized"

EXPECTED_ADMISSION_STATUS = OOP_002_ADMISSION_STATUS
EXPECTED_CONSUMER_ID = "oracle.operator.console.v1"
EXPECTED_PROJECTION = "operator_research"

MAX_QUERY_LENGTH = 4096
MAX_RESULT_LIMIT = 100
DEFAULT_RESULT_LIMIT = 25

_ALLOWED_QUERY_MODES = frozenset(
    {
        "market_lookup",
        "opportunity_lookup",
        "research_summary",
        "evidence_lookup",
        "comparison",
    }
)
_ALLOWED_SORT_ORDERS = frozenset(
    {
        "relevance",
        "priority",
        "confidence",
        "market_close_time",
    }
)
_ALLOWED_TIME_SCOPES = frozenset(
    {
        "same_day",
        "next_24_hours",
        "next_7_days",
        "all_authorized",
    }
)


class OracleOperatorQueryRequestInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorQueryRequestInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryRequestInvariantError(
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


def _normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise OracleOperatorQueryRequestInvariantError(
            "query text must be a string"
        )
    normalized = re.sub(r"\s+", " ", value).strip()
    if not normalized:
        raise OracleOperatorQueryRequestInvariantError(
            "query text must not be empty"
        )
    if len(normalized) > MAX_QUERY_LENGTH:
        raise OracleOperatorQueryRequestInvariantError(
            "query text exceeds maximum length"
        )
    return normalized


def _normalize_tags(values: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise OracleOperatorQueryRequestInvariantError(
                "query tags must be strings"
            )
        item = re.sub(r"\s+", " ", value).strip().lower()
        if not item:
            raise OracleOperatorQueryRequestInvariantError(
                "query tags must not be empty"
            )
        if len(item) > 128:
            raise OracleOperatorQueryRequestInvariantError(
                "query tag exceeds maximum length"
            )
        normalized.append(item)
    return tuple(sorted(set(normalized)))


@dataclass(frozen=True)
class OracleOperatorQueryRequest:
    query_request_id: str
    source_admission_id: str
    source_admission_hash: str
    source_dependency_receipt_id: str
    source_dependency_receipt_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    operator_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    admission_type_verified: bool
    admission_hash_verified: bool
    admission_status_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    query_mode_verified: bool
    time_scope_verified: bool
    sort_order_verified: bool
    result_limit_verified: bool
    authorized_scope_preserved: bool
    deterministic_request_verified: bool
    analytics_read_only_dependency_preserved: bool
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
    query_request_status: str
    query_request_hash: str


class OracleOperatorQueryRequestContract:
    @staticmethod
    def _verify_admission(
        admission: OracleOperatorAnalyticsDependencyAdmission,
    ) -> None:
        if not isinstance(
            admission,
            OracleOperatorAnalyticsDependencyAdmission,
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "source must be the canonical OOP-002 admission"
            )

        body = asdict(admission)
        supplied_hash = body.pop("admission_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission hash mismatch"
            )

        if not _valid_sha256(admission.admission_id):
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission identity is invalid"
            )
        if admission.admission_status != EXPECTED_ADMISSION_STATUS:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission is not active"
            )
        if admission.admitted_consumer_id != EXPECTED_CONSUMER_ID:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 consumer identity mismatch"
            )
        if admission.admitted_projection != EXPECTED_PROJECTION:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 projection identity mismatch"
            )

        if admission.admitted_entry_count < 1:
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission contains no entries"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_query_response_ids
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "query-response cardinality mismatch"
            )
        if len(
            set(admission.admitted_response_artifact_entry_ids)
        ) != admission.admitted_entry_count:
            raise OracleOperatorQueryRequestInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(
            set(admission.admitted_query_response_ids)
        ) != admission.admitted_entry_count:
            raise OracleOperatorQueryRequestInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            admission.dependency_receipt_type_verified,
            admission.dependency_receipt_hash_verified,
            admission.subsystem_boundary_verified,
            admission.source_schema_verified,
            admission.source_authorization_schema_verified,
            admission.consumer_identity_verified,
            admission.projection_identity_verified,
            admission.entry_cardinality_verified,
            admission.unique_entry_identities_verified,
            admission.source_lineage_verified,
            admission.deterministic_replay_verified,
            admission.read_only_dependency_verified,
            admission.operator_query_construction_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission is incomplete"
            )

        forbidden_authority = (
            admission.operator_session_construction_allowed,
            admission.operator_console_rendering_allowed,
            admission.operator_presentation_rendering_allowed,
            admission.analytics_reexecution_allowed,
            admission.analytics_reexecution_performed,
            admission.analytics_database_connection_allowed,
            admission.analytics_database_connection_performed,
            admission.analytics_mutation_allowed,
            admission.analytics_mutation_performed,
            admission.publication_allowed,
            admission.publication_performed,
            admission.qseries_handoff_allowed,
            admission.qseries_execution_allowed,
            admission.qseries_execution_performed,
            admission.order_creation_allowed,
            admission.order_creation_performed,
            admission.funds_movement_allowed,
            admission.funds_movement_performed,
            admission.portfolio_mutation_allowed,
            admission.portfolio_mutation_performed,
        )
        if any(forbidden_authority):
            raise OracleOperatorQueryRequestInvariantError(
                "OOP-002 admission contains forbidden authority or activity"
            )

    def materialize(
        self,
        *,
        admission: OracleOperatorAnalyticsDependencyAdmission,
        query_mode: str,
        query_text: str,
        time_scope: str = "all_authorized",
        sort_order: str = "relevance",
        result_limit: int = DEFAULT_RESULT_LIMIT,
        requested_tags: Sequence[str] = (),
    ) -> OracleOperatorQueryRequest:
        self._verify_admission(admission)

        if query_mode not in _ALLOWED_QUERY_MODES:
            raise OracleOperatorQueryRequestInvariantError(
                "unsupported query mode"
            )
        if time_scope not in _ALLOWED_TIME_SCOPES:
            raise OracleOperatorQueryRequestInvariantError(
                "unsupported time scope"
            )
        if sort_order not in _ALLOWED_SORT_ORDERS:
            raise OracleOperatorQueryRequestInvariantError(
                "unsupported sort order"
            )
        if (
            isinstance(result_limit, bool)
            or not isinstance(result_limit, int)
            or result_limit < 1
            or result_limit > MAX_RESULT_LIMIT
        ):
            raise OracleOperatorQueryRequestInvariantError(
                "result limit is outside the allowed range"
            )

        normalized_query_text = _normalize_text(query_text)
        normalized_tags = _normalize_tags(requested_tags)

        query_request_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_admission_id": admission.admission_id,
                "source_admission_hash": admission.admission_hash,
                "query_mode": query_mode,
                "query_text": normalized_query_text,
                "time_scope": time_scope,
                "sort_order": sort_order,
                "result_limit": result_limit,
                "requested_tags": normalized_tags,
                "authorized_response_artifact_entry_ids": (
                    admission.admitted_response_artifact_entry_ids
                ),
                "authorized_query_response_ids": (
                    admission.admitted_query_response_ids
                ),
            }
        )

        body = {
            "query_request_id": query_request_id,
            "source_admission_id": admission.admission_id,
            "source_admission_hash": admission.admission_hash,
            "source_dependency_receipt_id": (
                admission.source_dependency_receipt_id
            ),
            "source_dependency_receipt_hash": (
                admission.source_dependency_receipt_hash
            ),
            "source_authorization_id": admission.source_authorization_id,
            "source_authorization_hash": admission.source_authorization_hash,
            "operator_namespace": EXPECTED_OPERATOR_NAMESPACE,
            "consumer_id": admission.admitted_consumer_id,
            "projection": admission.admitted_projection,
            "query_mode": query_mode,
            "query_text": normalized_query_text,
            "time_scope": time_scope,
            "sort_order": sort_order,
            "result_limit": result_limit,
            "requested_tags": normalized_tags,
            "authorized_entry_count": admission.admitted_entry_count,
            "authorized_response_artifact_entry_ids": tuple(
                admission.admitted_response_artifact_entry_ids
            ),
            "authorized_query_response_ids": tuple(
                admission.admitted_query_response_ids
            ),
            "admission_type_verified": True,
            "admission_hash_verified": True,
            "admission_status_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "query_mode_verified": True,
            "time_scope_verified": True,
            "sort_order_verified": True,
            "result_limit_verified": True,
            "authorized_scope_preserved": True,
            "deterministic_request_verified": True,
            "analytics_read_only_dependency_preserved": True,
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
            "query_request_status": QUERY_REQUEST_STATUS,
        }

        return OracleOperatorQueryRequest(
            **body,
            query_request_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "QUERY_REQUEST_SCHEMA_VERSION",
    "QUERY_REQUEST_STATUS",
    "EXPECTED_ADMISSION_STATUS",
    "EXPECTED_CONSUMER_ID",
    "EXPECTED_PROJECTION",
    "MAX_QUERY_LENGTH",
    "MAX_RESULT_LIMIT",
    "DEFAULT_RESULT_LIMIT",
    "OracleOperatorQueryRequest",
    "OracleOperatorQueryRequestContract",
    "OracleOperatorQueryRequestInvariantError",
    "stable_hash",
]
