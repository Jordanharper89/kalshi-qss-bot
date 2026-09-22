from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate import (
    EXECUTION_MODE as OOP_011_EXECUTION_MODE,
    READINESS_STATUS as OOP_011_READINESS_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness,
)

SCHEMA_VERSION = "OOP-012"
ENGINE_ID = "OOP-012"
POLICY_ID = (
    "oracle.operator.query-resolution-adapter-invocation-execution-authorization-gate.v1"
)
AUTHORIZATION_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-adapter-invocation-execution-authorization.v1"
)
AUTHORIZATION_STATUS = (
    "operator_query_resolution_adapter_invocation_execution_authorized"
)

EXPECTED_READINESS_STATUS = OOP_011_READINESS_STATUS
EXPECTED_EXECUTION_MODE = OOP_011_EXECUTION_MODE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
    RuntimeError
):
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
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
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
class OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorization:
    adapter_execution_authorization_id: str
    source_adapter_execution_readiness_id: str
    source_adapter_execution_readiness_hash: str
    source_read_consumption_id: str
    source_read_consumption_hash: str
    source_read_authorization_id: str
    source_read_authorization_hash: str
    source_read_readiness_id: str
    source_read_readiness_hash: str
    source_resolution_consumption_id: str
    source_resolution_consumption_hash: str
    source_resolution_authorization_id: str
    source_resolution_authorization_hash: str
    source_resolution_plan_id: str
    source_resolution_plan_hash: str
    source_query_admission_id: str
    source_query_admission_hash: str
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
    invocation_package_type: str
    read_invocation_mode: str
    read_adapter_contract_id: str
    execution_mode: str
    authorized_resolution_strategy: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    readiness_type_verified: bool
    readiness_identity_verified: bool
    readiness_hash_verified: bool
    readiness_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_invocation_package_verified: bool
    read_adapter_contract_verified: bool
    bounded_artifact_read_verified: bool
    single_read_invocation_verified: bool
    deterministic_authorization_verified: bool
    adapter_invocation_execution_ready: bool
    adapter_invocation_execution_authorized: bool
    adapter_invocation_execution_allowed: bool
    adapter_invocation_execution_performed: bool
    analytics_artifact_read_allowed: bool
    analytics_artifact_read_performed: bool
    analytics_query_execution_allowed: bool
    analytics_query_execution_performed: bool
    analytics_reexecution_allowed: bool
    analytics_reexecution_performed: bool
    analytics_database_connection_allowed: bool
    analytics_database_connection_performed: bool
    analytics_mutation_allowed: bool
    analytics_mutation_performed: bool
    research_response_materialization_allowed: bool
    research_response_materialization_performed: bool
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
    authorization_status: str
    adapter_execution_authorization_hash: str


class OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationGate:
    @staticmethod
    def _verify_readiness(
        readiness: OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness,
    ) -> None:
        if not isinstance(
            readiness,
            OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness,
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "source must be the canonical OOP-011 execution-readiness record"
            )

        body = asdict(readiness)
        supplied_hash = body.pop("adapter_execution_readiness_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "OOP-011 readiness hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "OOP-011 readiness hash mismatch"
            )

        required_hashes = (
            readiness.adapter_execution_readiness_id,
            readiness.source_read_consumption_hash,
            readiness.source_read_authorization_hash,
            readiness.source_read_readiness_hash,
            readiness.source_resolution_consumption_hash,
            readiness.source_resolution_authorization_hash,
            readiness.source_resolution_plan_hash,
            readiness.source_query_admission_hash,
            readiness.source_query_request_hash,
            readiness.source_admission_hash,
            readiness.source_dependency_receipt_hash,
            readiness.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "OOP-011 lineage contains invalid hashes"
            )

        if readiness.readiness_status != EXPECTED_READINESS_STATUS:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "OOP-011 readiness record is not active"
            )
        if readiness.execution_mode != EXPECTED_EXECUTION_MODE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "execution mode mismatch"
            )
        if readiness.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if readiness.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "query namespace mismatch"
            )

        if readiness.ready_entry_count < 1:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "readiness record contains no entries"
            )
        if readiness.ready_entry_count != len(
            readiness.ready_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if readiness.ready_entry_count != len(readiness.ready_query_response_ids):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(readiness.ready_response_artifact_entry_ids)) != readiness.ready_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(readiness.ready_query_response_ids)) != readiness.ready_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            readiness.consumption_type_verified,
            readiness.consumption_identity_verified,
            readiness.consumption_hash_verified,
            readiness.consumption_status_verified,
            readiness.complete_lineage_verified,
            readiness.namespaces_verified,
            readiness.query_parameters_verified,
            readiness.frozen_scope_verified,
            readiness.frozen_scope_preserved,
            readiness.immutable_invocation_package_verified,
            readiness.read_adapter_contract_verified,
            readiness.bounded_artifact_read_verified,
            readiness.single_read_invocation_verified,
            readiness.deterministic_readiness_verified,
            readiness.adapter_invocation_execution_ready,
            readiness.adapter_invocation_execution_allowed,
            readiness.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "OOP-011 readiness record is incomplete"
            )

        forbidden_activity = (
            readiness.adapter_invocation_execution_performed,
            readiness.analytics_artifact_read_performed,
            readiness.analytics_query_execution_allowed,
            readiness.analytics_query_execution_performed,
            readiness.analytics_reexecution_allowed,
            readiness.analytics_reexecution_performed,
            readiness.analytics_database_connection_allowed,
            readiness.analytics_database_connection_performed,
            readiness.analytics_mutation_allowed,
            readiness.analytics_mutation_performed,
            readiness.operator_session_construction_allowed,
            readiness.operator_console_rendering_allowed,
            readiness.operator_presentation_rendering_allowed,
            readiness.publication_allowed,
            readiness.publication_performed,
            readiness.qseries_handoff_allowed,
            readiness.qseries_execution_allowed,
            readiness.qseries_execution_performed,
            readiness.order_creation_allowed,
            readiness.order_creation_performed,
            readiness.funds_movement_allowed,
            readiness.funds_movement_performed,
            readiness.portfolio_mutation_allowed,
            readiness.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError(
                "OOP-011 readiness record contains forbidden activity"
            )

    def authorize(
        self,
        *,
        readiness: OracleOperatorQueryResolutionAdapterInvocationExecutionReadiness,
    ) -> OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorization:
        self._verify_readiness(readiness)

        adapter_execution_authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_adapter_execution_readiness_id": (
                    readiness.adapter_execution_readiness_id
                ),
                "source_adapter_execution_readiness_hash": (
                    readiness.adapter_execution_readiness_hash
                ),
                "execution_mode": readiness.execution_mode,
                "read_adapter_contract_id": readiness.read_adapter_contract_id,
                "authorized_resolution_strategy": readiness.ready_resolution_strategy,
                "query_mode": readiness.query_mode,
                "query_text": readiness.query_text,
                "time_scope": readiness.time_scope,
                "sort_order": readiness.sort_order,
                "result_limit": readiness.result_limit,
                "requested_tags": readiness.requested_tags,
                "authorized_response_artifact_entry_ids": (
                    readiness.ready_response_artifact_entry_ids
                ),
                "authorized_query_response_ids": (
                    readiness.ready_query_response_ids
                ),
            }
        )

        body = {
            "adapter_execution_authorization_id": adapter_execution_authorization_id,
            "source_adapter_execution_readiness_id": readiness.adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": readiness.adapter_execution_readiness_hash,
            "source_read_consumption_id": readiness.source_read_consumption_id,
            "source_read_consumption_hash": readiness.source_read_consumption_hash,
            "source_read_authorization_id": readiness.source_read_authorization_id,
            "source_read_authorization_hash": readiness.source_read_authorization_hash,
            "source_read_readiness_id": readiness.source_read_readiness_id,
            "source_read_readiness_hash": readiness.source_read_readiness_hash,
            "source_resolution_consumption_id": readiness.source_resolution_consumption_id,
            "source_resolution_consumption_hash": readiness.source_resolution_consumption_hash,
            "source_resolution_authorization_id": readiness.source_resolution_authorization_id,
            "source_resolution_authorization_hash": readiness.source_resolution_authorization_hash,
            "source_resolution_plan_id": readiness.source_resolution_plan_id,
            "source_resolution_plan_hash": readiness.source_resolution_plan_hash,
            "source_query_admission_id": readiness.source_query_admission_id,
            "source_query_admission_hash": readiness.source_query_admission_hash,
            "source_query_request_id": readiness.source_query_request_id,
            "source_query_request_hash": readiness.source_query_request_hash,
            "source_admission_id": readiness.source_admission_id,
            "source_admission_hash": readiness.source_admission_hash,
            "source_dependency_receipt_id": readiness.source_dependency_receipt_id,
            "source_dependency_receipt_hash": readiness.source_dependency_receipt_hash,
            "source_authorization_id": readiness.source_authorization_id,
            "source_authorization_hash": readiness.source_authorization_hash,
            "operator_namespace": readiness.operator_namespace,
            "query_namespace": readiness.query_namespace,
            "consumer_id": readiness.consumer_id,
            "projection": readiness.projection,
            "query_mode": readiness.query_mode,
            "query_text": readiness.query_text,
            "time_scope": readiness.time_scope,
            "sort_order": readiness.sort_order,
            "result_limit": readiness.result_limit,
            "requested_tags": tuple(readiness.requested_tags),
            "invocation_package_type": readiness.invocation_package_type,
            "read_invocation_mode": readiness.read_invocation_mode,
            "read_adapter_contract_id": readiness.read_adapter_contract_id,
            "execution_mode": readiness.execution_mode,
            "authorized_resolution_strategy": readiness.ready_resolution_strategy,
            "authorized_entry_count": readiness.ready_entry_count,
            "authorized_response_artifact_entry_ids": tuple(
                readiness.ready_response_artifact_entry_ids
            ),
            "authorized_query_response_ids": tuple(
                readiness.ready_query_response_ids
            ),
            "readiness_type_verified": True,
            "readiness_identity_verified": True,
            "readiness_hash_verified": True,
            "readiness_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_invocation_package_verified": True,
            "read_adapter_contract_verified": True,
            "bounded_artifact_read_verified": True,
            "single_read_invocation_verified": True,
            "deterministic_authorization_verified": True,
            "adapter_invocation_execution_ready": True,
            "adapter_invocation_execution_authorized": True,
            "adapter_invocation_execution_allowed": True,
            "adapter_invocation_execution_performed": False,
            "analytics_artifact_read_allowed": True,
            "analytics_artifact_read_performed": False,
            "analytics_query_execution_allowed": False,
            "analytics_query_execution_performed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_allowed": False,
            "analytics_database_connection_performed": False,
            "analytics_mutation_allowed": False,
            "analytics_mutation_performed": False,
            "research_response_materialization_allowed": False,
            "research_response_materialization_performed": False,
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
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorization(
            **body,
            adapter_execution_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "EXPECTED_READINESS_STATUS",
    "EXPECTED_EXECUTION_MODE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorization",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationGate",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError",
    "stable_hash",
]
