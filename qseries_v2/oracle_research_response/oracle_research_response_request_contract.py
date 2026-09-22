from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_runtime_read_only_dependency_gate import (
    DEPENDENCY_STATUS as ORR_001_DEPENDENCY_STATUS,
    DEPENDENCY_TYPE as ORR_001_DEPENDENCY_TYPE,
    SUBSYSTEM_NAMESPACE,
    OracleResearchResponseRuntimeDependencyReceipt,
)

SCHEMA_VERSION = "ORR-002"
ENGINE_ID = "ORR-002"
POLICY_ID = "oracle.research-response.request-contract.v1"
REQUEST_TYPE = "oracle_research_response_read_only_request"
REQUEST_STATUS = "oracle_research_response_request_materialized"

RESPONSE_MODE_RESEARCH_ANSWER = "research_answer"
RESPONSE_MODE_PREDICTION_CARD = "prediction_card"
RESPONSE_MODE_MARKET_DEEP_DIVE = "market_deep_dive"
RESPONSE_MODE_COMPARISON = "comparison"
RESPONSE_MODE_EVIDENCE_SUMMARY = "evidence_summary"

ALLOWED_RESPONSE_MODES = (
    RESPONSE_MODE_RESEARCH_ANSWER,
    RESPONSE_MODE_PREDICTION_CARD,
    RESPONSE_MODE_MARKET_DEEP_DIVE,
    RESPONSE_MODE_COMPARISON,
    RESPONSE_MODE_EVIDENCE_SUMMARY,
)

MAX_QUESTION_LENGTH = 4000
MAX_FILTER_ITEMS = 32
MAX_FILTER_VALUE_LENGTH = 256


class OracleResearchResponseRequestInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleResearchResponseRequestInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseRequestInvariantError(
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


def _normalized_required_text(name: str, value: Any, maximum: int) -> str:
    if not isinstance(value, str):
        raise OracleResearchResponseRequestInvariantError(f"{name} must be text")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise OracleResearchResponseRequestInvariantError(f"{name} cannot be empty")
    if len(normalized) > maximum:
        raise OracleResearchResponseRequestInvariantError(
            f"{name} exceeds maximum length {maximum}"
        )
    return normalized


def _normalized_filters(filters: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    if filters is None:
        return ()
    if not isinstance(filters, Mapping):
        raise OracleResearchResponseRequestInvariantError(
            "filters must be a string mapping"
        )
    if len(filters) > MAX_FILTER_ITEMS:
        raise OracleResearchResponseRequestInvariantError(
            "too many request filters"
        )

    normalized: list[tuple[str, str]] = []
    for raw_key, raw_value in filters.items():
        key = _normalized_required_text(
            "filter key",
            raw_key,
            MAX_FILTER_VALUE_LENGTH,
        ).lower().replace(" ", "_")
        value = _normalized_required_text(
            f"filter value for {key}",
            raw_value,
            MAX_FILTER_VALUE_LENGTH,
        )
        normalized.append((key, value))

    normalized.sort()
    if len({key for key, _ in normalized}) != len(normalized):
        raise OracleResearchResponseRequestInvariantError(
            "duplicate normalized filter key"
        )
    return tuple(normalized)


@dataclass(frozen=True)
class OracleResearchResponseRequest:
    request_id: str
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
    dependency_identity_verified: bool
    dependency_hash_verified: bool
    dependency_contract_verified: bool
    typed_question_verified: bool
    response_mode_verified: bool
    filter_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_request_boundary_verified: bool
    read_only_boundary_verified: bool
    request_single_use_verified: bool
    duplicate_request_allowed: bool
    request_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    request_type: str
    request_status: str
    request_hash: str


class OracleResearchResponseRequestContract:
    def materialize(
        self,
        *,
        dependency_receipt: OracleResearchResponseRuntimeDependencyReceipt,
        requester_id: str,
        correlation_id: str,
        question_text: str,
        response_mode: str,
        requested_at: datetime,
        filters: Mapping[str, str] | None = None,
    ) -> OracleResearchResponseRequest:
        if not isinstance(
            dependency_receipt,
            OracleResearchResponseRuntimeDependencyReceipt,
        ):
            raise OracleResearchResponseRequestInvariantError(
                "dependency_receipt must be canonical ORR-001 receipt"
            )

        dependency_body = asdict(dependency_receipt)
        supplied_dependency_hash = dependency_body.pop(
            "dependency_receipt_hash",
            None,
        )
        if (
            not _valid_sha256(supplied_dependency_hash)
            or stable_hash(dependency_body) != supplied_dependency_hash
        ):
            raise OracleResearchResponseRequestInvariantError(
                "ORR-001 dependency receipt hash mismatch"
            )

        dependency_required = (
            _valid_sha256(dependency_receipt.dependency_receipt_id),
            _valid_sha256(dependency_receipt.source_runtime_completion_id),
            _valid_sha256(dependency_receipt.source_runtime_completion_hash),
            dependency_receipt.subsystem_namespace == SUBSYSTEM_NAMESPACE,
            dependency_receipt.dependency_type == ORR_001_DEPENDENCY_TYPE,
            dependency_receipt.dependency_status == ORR_001_DEPENDENCY_STATUS,
            dependency_receipt.complete_runtime_lineage_verified,
            dependency_receipt.source_runtime_complete_verified,
            dependency_receipt.source_runtime_immutable_freeze_verified,
            dependency_receipt.source_runtime_read_only_verified,
            dependency_receipt.downstream_read_only_operation_verified,
            dependency_receipt.deterministic_boundary_verified,
            dependency_receipt.immutable_result_boundary_verified,
            dependency_receipt.dependency_single_use_verified,
            not dependency_receipt.duplicate_dependency_allowed,
            not dependency_receipt.dependency_reversible,
        )
        forbidden_dependency = (
            dependency_receipt.runtime_serving_allowed,
            dependency_receipt.network_listener_allowed,
            dependency_receipt.database_connection_allowed,
            dependency_receipt.publication_allowed,
            dependency_receipt.qseries_handoff_allowed,
            dependency_receipt.qseries_execution_allowed,
            dependency_receipt.order_creation_allowed,
            dependency_receipt.funds_movement_allowed,
            dependency_receipt.portfolio_mutation_allowed,
        )
        if not all(dependency_required) or any(forbidden_dependency):
            raise OracleResearchResponseRequestInvariantError(
                "ORR-001 dependency contract incomplete or unsafe"
            )

        requester = _normalized_required_text("requester_id", requester_id, 256)
        correlation = _normalized_required_text(
            "correlation_id",
            correlation_id,
            256,
        )
        question = _normalized_required_text(
            "question_text",
            question_text,
            MAX_QUESTION_LENGTH,
        )

        if response_mode not in ALLOWED_RESPONSE_MODES:
            raise OracleResearchResponseRequestInvariantError(
                "unsupported response_mode"
            )
        normalized_filters = _normalized_filters(filters)

        if (
            not isinstance(requested_at, datetime)
            or requested_at.tzinfo is None
            or requested_at.utcoffset() is None
        ):
            raise OracleResearchResponseRequestInvariantError(
                "requested_at must be timezone-aware"
            )
        at = requested_at.astimezone(timezone.utc)

        body = {
            "dependency_receipt_id": dependency_receipt.dependency_receipt_id,
            "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,
            "source_runtime_completion_id": dependency_receipt.source_runtime_completion_id,
            "source_runtime_completion_hash": dependency_receipt.source_runtime_completion_hash,
            "subsystem_namespace": SUBSYSTEM_NAMESPACE,
            "requester_id": requester,
            "correlation_id": correlation,
            "question_text": question,
            "response_mode": response_mode,
            "filters": normalized_filters,
            "requested_at": at,
            "dependency_identity_verified": True,
            "dependency_hash_verified": True,
            "dependency_contract_verified": True,
            "typed_question_verified": True,
            "response_mode_verified": True,
            "filter_boundary_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_request_boundary_verified": True,
            "read_only_boundary_verified": True,
            "request_single_use_verified": True,
            "duplicate_request_allowed": False,
            "request_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "request_type": REQUEST_TYPE,
            "request_status": REQUEST_STATUS,
        }
        body["request_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "dependency_receipt_id": dependency_receipt.dependency_receipt_id,
                "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,
                "requester_id": requester,
                "correlation_id": correlation,
                "question_text": question,
                "response_mode": response_mode,
                "filters": normalized_filters,
                "requested_at": at,
                "request_type": REQUEST_TYPE,
            }
        )
        return OracleResearchResponseRequest(
            **body,
            request_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "REQUEST_TYPE",
    "REQUEST_STATUS",
    "RESPONSE_MODE_RESEARCH_ANSWER",
    "RESPONSE_MODE_PREDICTION_CARD",
    "RESPONSE_MODE_MARKET_DEEP_DIVE",
    "RESPONSE_MODE_COMPARISON",
    "RESPONSE_MODE_EVIDENCE_SUMMARY",
    "ALLOWED_RESPONSE_MODES",
    "MAX_QUESTION_LENGTH",
    "MAX_FILTER_ITEMS",
    "MAX_FILTER_VALUE_LENGTH",
    "OracleResearchResponseRequestInvariantError",
    "OracleResearchResponseRequest",
    "OracleResearchResponseRequestContract",
    "stable_hash",
]
