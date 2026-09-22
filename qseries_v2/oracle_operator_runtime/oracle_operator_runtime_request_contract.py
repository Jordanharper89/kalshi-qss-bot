from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_certified_read_only_dependency_gate import (
    DEPENDENCY_STATUS as OOR_001_DEPENDENCY_STATUS,
    DEPENDENCY_TYPE as OOR_001_DEPENDENCY_TYPE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
)

SCHEMA_VERSION = "OOR-002"
ENGINE_ID = "OOR-002"
POLICY_ID = "oracle.operator-runtime-request-contract.v1"
REQUEST_TYPE = "oracle_operator_runtime_read_only_request"
REQUEST_STATUS = "oracle_operator_runtime_request_materialized"
CONSUMER_ID = "oracle.operator.runtime.v1"
PROJECTION = "certified_operator_read_only"

_ALLOWED_MODES = frozenset({"query", "session", "console", "presentation"})
_TOKEN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")


class OracleOperatorRuntimeRequestInvariantError(ValueError):
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
            raise OracleOperatorRuntimeRequestInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeRequestInvariantError(
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


def _clean_text(value: Any, *, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise OracleOperatorRuntimeRequestInvariantError(f"{field} must be a string")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > maximum:
        raise OracleOperatorRuntimeRequestInvariantError(
            f"{field} must contain 1 through {maximum} normalized characters"
        )
    return cleaned


@dataclass(frozen=True)
class OracleOperatorRuntimeRequest:
    request_id: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_operator_completion_certification_id: str
    runtime_namespace: str
    requester_id: str
    correlation_id: str
    mode: str
    query_text: str
    requested_at: datetime
    read_only_required: bool
    deterministic_required: bool
    immutable_result_required: bool
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


class OracleOperatorRuntimeRequestContract:
    @staticmethod
    def _verify_dependency(
        receipt: OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
    ) -> None:
        if not isinstance(receipt, OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt):
            raise OracleOperatorRuntimeRequestInvariantError(
                "dependency must be canonical OOR-001 receipt"
            )
        body = asdict(receipt)
        supplied_hash = body.pop("dependency_receipt_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeRequestInvariantError(
                "OOR-001 dependency receipt hash mismatch"
            )
        required = (
            receipt.dependency_status == OOR_001_DEPENDENCY_STATUS,
            receipt.dependency_type == OOR_001_DEPENDENCY_TYPE,
            receipt.runtime_namespace == RUNTIME_NAMESPACE,
            receipt.consumer_id == CONSUMER_ID,
            receipt.projection == PROJECTION,
            receipt.source_operator_subsystem_completion_certified,
            receipt.source_operator_subsystem_frozen,
            not receipt.source_further_operator_builds_required,
            receipt.certification_hash_verified,
            receipt.freeze_record_payload_hash_verified,
            receipt.complete_operator_lineage_verified,
            receipt.operator_completion_verified,
            receipt.operator_freeze_verified,
            receipt.deterministic_dependency_verified,
            receipt.immutable_dependency_verified,
            receipt.read_only_dependency_verified,
            receipt.runtime_subsystem_root_established,
        )
        if not all(required):
            raise OracleOperatorRuntimeRequestInvariantError(
                "OOR-001 dependency receipt is incomplete"
            )
        forbidden = (
            receipt.runtime_serving_allowed,
            receipt.runtime_serving_performed,
            receipt.network_listener_allowed,
            receipt.network_listener_started,
            receipt.operator_reexecution_allowed,
            receipt.operator_reexecution_performed,
            receipt.analytics_reexecution_allowed,
            receipt.analytics_reexecution_performed,
            receipt.database_connection_allowed,
            receipt.database_connection_performed,
            receipt.publication_allowed,
            receipt.publication_performed,
            receipt.qseries_handoff_allowed,
            receipt.qseries_execution_allowed,
            receipt.qseries_execution_performed,
            receipt.order_creation_allowed,
            receipt.order_creation_performed,
            receipt.funds_movement_allowed,
            receipt.funds_movement_performed,
            receipt.portfolio_mutation_allowed,
            receipt.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeRequestInvariantError(
                "forbidden OOR-001 dependency state detected"
            )

    def materialize(
        self,
        *,
        dependency_receipt: OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
        requester_id: str,
        correlation_id: str,
        mode: str,
        query_text: str,
        requested_at: datetime,
    ) -> OracleOperatorRuntimeRequest:
        self._verify_dependency(dependency_receipt)

        requester = _clean_text(requester_id, field="requester_id", maximum=128)
        correlation = _clean_text(correlation_id, field="correlation_id", maximum=128)
        if not _TOKEN.fullmatch(requester):
            raise OracleOperatorRuntimeRequestInvariantError("requester_id is not canonical")
        if not _TOKEN.fullmatch(correlation):
            raise OracleOperatorRuntimeRequestInvariantError("correlation_id is not canonical")
        if mode not in _ALLOWED_MODES:
            raise OracleOperatorRuntimeRequestInvariantError("unsupported runtime request mode")
        query = _clean_text(query_text, field="query_text", maximum=4096)
        if not isinstance(requested_at, datetime) or requested_at.tzinfo is None or requested_at.utcoffset() is None:
            raise OracleOperatorRuntimeRequestInvariantError(
                "requested_at must be timezone-aware"
            )
        normalized_time = requested_at.astimezone(timezone.utc)

        request_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "dependency_receipt_id": dependency_receipt.dependency_receipt_id,
                "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,
                "requester_id": requester,
                "correlation_id": correlation,
                "mode": mode,
                "query_text": query,
                "requested_at": normalized_time,
                "request_type": REQUEST_TYPE,
            }
        )
        body = {
            "request_id": request_id,
            "dependency_receipt_id": dependency_receipt.dependency_receipt_id,
            "dependency_receipt_hash": dependency_receipt.dependency_receipt_hash,
            "source_operator_completion_certification_id": dependency_receipt.source_operator_completion_certification_id,
            "runtime_namespace": RUNTIME_NAMESPACE,
            "requester_id": requester,
            "correlation_id": correlation,
            "mode": mode,
            "query_text": query,
            "requested_at": normalized_time,
            "read_only_required": True,
            "deterministic_required": True,
            "immutable_result_required": True,
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
        return OracleOperatorRuntimeRequest(
            **body,
            request_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "REQUEST_TYPE",
    "REQUEST_STATUS",
    "CONSUMER_ID",
    "PROJECTION",
    "OracleOperatorRuntimeRequest",
    "OracleOperatorRuntimeRequestContract",
    "OracleOperatorRuntimeRequestInvariantError",
    "stable_hash",
]
