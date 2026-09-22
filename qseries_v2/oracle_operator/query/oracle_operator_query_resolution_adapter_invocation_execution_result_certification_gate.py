from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    EXECUTION_RESULT_TYPE as OOP_015_EXECUTION_RESULT_TYPE,
    EXECUTION_STATUS as OOP_015_EXECUTION_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecution,
)

SCHEMA_VERSION = "OOP-016"
ENGINE_ID = "OOP-016"
POLICY_ID = (
    "oracle.operator.query-resolution-adapter-invocation-execution-result-certification-gate.v1"
)
CERTIFICATION_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-adapter-invocation-execution-result-certification.v1"
)
CERTIFICATION_STATUS = (
    "operator_query_resolution_adapter_invocation_execution_result_certified"
)
CERTIFIED_RESULT_TYPE = "immutable_certified_bounded_read_only_adapter_result"

EXPECTED_EXECUTION_STATUS = OOP_015_EXECUTION_STATUS
EXPECTED_EXECUTION_RESULT_TYPE = OOP_015_EXECUTION_RESULT_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
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
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
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
class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification:
    execution_result_certification_id: str
    source_adapter_invocation_execution_id: str
    source_adapter_invocation_execution_hash: str
    source_adapter_invocation_activation_id: str
    source_adapter_invocation_activation_hash: str
    source_adapter_execution_consumption_id: str
    source_adapter_execution_consumption_hash: str
    source_adapter_execution_authorization_id: str
    source_adapter_execution_authorization_hash: str
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
    execution_package_type: str
    active_invocation_type: str
    execution_result_type: str
    certified_result_type: str
    read_invocation_mode: str
    read_adapter_contract_id: str
    execution_mode: str
    certified_resolution_strategy: str
    certified_entry_count: int
    certified_response_artifact_entry_ids: tuple[str, ...]
    certified_query_response_ids: tuple[str, ...]
    certified_result_count: int
    certified_result_hashes: tuple[str, ...]
    certified_result_payloads: tuple[Mapping[str, Any], ...]
    execution_type_verified: bool
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_invocation_package_verified: bool
    immutable_execution_package_verified: bool
    execution_result_type_verified: bool
    read_adapter_contract_verified: bool
    bounded_artifact_read_verified: bool
    single_read_invocation_verified: bool
    execution_performed_verified: bool
    artifact_read_performed_verified: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    deterministic_certification_verified: bool
    adapter_invocation_active: bool
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
    certification_status: str
    execution_result_certification_hash: str


class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate:
    @staticmethod
    def _verify_execution(
        execution: OracleOperatorQueryResolutionAdapterInvocationExecution,
    ) -> None:
        if not isinstance(
            execution,
            OracleOperatorQueryResolutionAdapterInvocationExecution,
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "source must be the canonical OOP-015 execution result"
            )

        body = asdict(execution)
        supplied_hash = body.pop("adapter_invocation_execution_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution hash mismatch"
            )

        required_hashes = (
            execution.adapter_invocation_execution_id,
            execution.source_adapter_invocation_activation_hash,
            execution.source_adapter_execution_consumption_hash,
            execution.source_adapter_execution_authorization_hash,
            execution.source_adapter_execution_readiness_hash,
            execution.source_read_consumption_hash,
            execution.source_read_authorization_hash,
            execution.source_read_readiness_hash,
            execution.source_resolution_consumption_hash,
            execution.source_resolution_authorization_hash,
            execution.source_resolution_plan_hash,
            execution.source_query_admission_hash,
            execution.source_query_request_hash,
            execution.source_admission_hash,
            execution.source_dependency_receipt_hash,
            execution.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 lineage contains invalid hashes"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution is not complete"
            )
        if execution.execution_result_type != EXPECTED_EXECUTION_RESULT_TYPE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "execution result type mismatch"
            )
        if execution.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "operator namespace mismatch"
            )
        if execution.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "query namespace mismatch"
            )

        if execution.executed_entry_count < 1:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "execution contains no entries"
            )
        if execution.executed_entry_count != execution.result_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "execution/result cardinality mismatch"
            )
        if execution.result_count != len(execution.result_payloads):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "result payload cardinality mismatch"
            )
        if execution.result_count != len(execution.result_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "result hash cardinality mismatch"
            )
        if execution.executed_entry_count != len(
            execution.executed_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if execution.executed_entry_count != len(
            execution.executed_query_response_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(execution.executed_response_artifact_entry_ids)) != execution.executed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(execution.executed_query_response_ids)) != execution.executed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "duplicate query-response identities detected"
            )

        recomputed_hashes = tuple(stable_hash(item) for item in execution.result_payloads)
        if recomputed_hashes != tuple(execution.result_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "result payload hash mismatch"
            )

        for index, payload in enumerate(execution.result_payloads):
            if not isinstance(payload, Mapping):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                    "result payload must be a mapping"
                )
            if (
                payload.get("response_artifact_entry_id")
                != execution.executed_response_artifact_entry_ids[index]
            ):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                    "result artifact-entry identity mismatch"
                )
            if (
                payload.get("query_response_id")
                != execution.executed_query_response_ids[index]
            ):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                    "result query-response identity mismatch"
                )

        required_truths = (
            execution.activation_type_verified,
            execution.activation_identity_verified,
            execution.activation_hash_verified,
            execution.activation_status_verified,
            execution.complete_lineage_verified,
            execution.namespaces_verified,
            execution.query_parameters_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.immutable_invocation_package_verified,
            execution.immutable_execution_package_verified,
            execution.read_adapter_contract_verified,
            execution.bounded_artifact_read_verified,
            execution.single_read_invocation_verified,
            execution.adapter_result_cardinality_verified,
            execution.adapter_result_identity_verified,
            execution.deterministic_execution_verified,
            execution.adapter_invocation_active,
            execution.adapter_invocation_execution_ready,
            execution.adapter_invocation_execution_authorized,
            execution.adapter_invocation_execution_allowed,
            execution.adapter_invocation_execution_performed,
            execution.analytics_artifact_read_allowed,
            execution.analytics_artifact_read_performed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution is incomplete"
            )

        forbidden_activity = (
            execution.analytics_query_execution_allowed,
            execution.analytics_query_execution_performed,
            execution.analytics_reexecution_allowed,
            execution.analytics_reexecution_performed,
            execution.analytics_database_connection_allowed,
            execution.analytics_database_connection_performed,
            execution.analytics_mutation_allowed,
            execution.analytics_mutation_performed,
            execution.research_response_materialization_allowed,
            execution.research_response_materialization_performed,
            execution.operator_session_construction_allowed,
            execution.operator_console_rendering_allowed,
            execution.operator_presentation_rendering_allowed,
            execution.publication_allowed,
            execution.publication_performed,
            execution.qseries_handoff_allowed,
            execution.qseries_execution_allowed,
            execution.qseries_execution_performed,
            execution.order_creation_allowed,
            execution.order_creation_performed,
            execution.funds_movement_allowed,
            execution.funds_movement_performed,
            execution.portfolio_mutation_allowed,
            execution.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution contains forbidden activity"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorQueryResolutionAdapterInvocationExecution,
    ) -> OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification:
        self._verify_execution(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_adapter_invocation_execution_id": (
                    execution.adapter_invocation_execution_id
                ),
                "source_adapter_invocation_execution_hash": (
                    execution.adapter_invocation_execution_hash
                ),
                "certified_result_type": CERTIFIED_RESULT_TYPE,
                "read_adapter_contract_id": execution.read_adapter_contract_id,
                "execution_mode": execution.execution_mode,
                "certified_response_artifact_entry_ids": (
                    execution.executed_response_artifact_entry_ids
                ),
                "certified_query_response_ids": execution.executed_query_response_ids,
                "certified_result_hashes": execution.result_hashes,
            }
        )

        body = {
            "execution_result_certification_id": certification_id,
            "source_adapter_invocation_execution_id": execution.adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": execution.adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": execution.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": execution.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": execution.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": execution.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": execution.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": execution.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": execution.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": execution.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": execution.source_read_consumption_id,
            "source_read_consumption_hash": execution.source_read_consumption_hash,
            "source_read_authorization_id": execution.source_read_authorization_id,
            "source_read_authorization_hash": execution.source_read_authorization_hash,
            "source_read_readiness_id": execution.source_read_readiness_id,
            "source_read_readiness_hash": execution.source_read_readiness_hash,
            "source_resolution_consumption_id": execution.source_resolution_consumption_id,
            "source_resolution_consumption_hash": execution.source_resolution_consumption_hash,
            "source_resolution_authorization_id": execution.source_resolution_authorization_id,
            "source_resolution_authorization_hash": execution.source_resolution_authorization_hash,
            "source_resolution_plan_id": execution.source_resolution_plan_id,
            "source_resolution_plan_hash": execution.source_resolution_plan_hash,
            "source_query_admission_id": execution.source_query_admission_id,
            "source_query_admission_hash": execution.source_query_admission_hash,
            "source_query_request_id": execution.source_query_request_id,
            "source_query_request_hash": execution.source_query_request_hash,
            "source_admission_id": execution.source_admission_id,
            "source_admission_hash": execution.source_admission_hash,
            "source_dependency_receipt_id": execution.source_dependency_receipt_id,
            "source_dependency_receipt_hash": execution.source_dependency_receipt_hash,
            "source_authorization_id": execution.source_authorization_id,
            "source_authorization_hash": execution.source_authorization_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "consumer_id": execution.consumer_id,
            "projection": execution.projection,
            "query_mode": execution.query_mode,
            "query_text": execution.query_text,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "invocation_package_type": execution.invocation_package_type,
            "execution_package_type": execution.execution_package_type,
            "active_invocation_type": execution.active_invocation_type,
            "execution_result_type": execution.execution_result_type,
            "certified_result_type": CERTIFIED_RESULT_TYPE,
            "read_invocation_mode": execution.read_invocation_mode,
            "read_adapter_contract_id": execution.read_adapter_contract_id,
            "execution_mode": execution.execution_mode,
            "certified_resolution_strategy": execution.executed_resolution_strategy,
            "certified_entry_count": execution.executed_entry_count,
            "certified_response_artifact_entry_ids": tuple(
                execution.executed_response_artifact_entry_ids
            ),
            "certified_query_response_ids": tuple(
                execution.executed_query_response_ids
            ),
            "certified_result_count": execution.result_count,
            "certified_result_hashes": tuple(execution.result_hashes),
            "certified_result_payloads": tuple(execution.result_payloads),
            "execution_type_verified": True,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_invocation_package_verified": True,
            "immutable_execution_package_verified": True,
            "execution_result_type_verified": True,
            "read_adapter_contract_verified": True,
            "bounded_artifact_read_verified": True,
            "single_read_invocation_verified": True,
            "execution_performed_verified": True,
            "artifact_read_performed_verified": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "deterministic_certification_verified": True,
            "adapter_invocation_active": True,
            "adapter_invocation_execution_ready": True,
            "adapter_invocation_execution_authorized": True,
            "adapter_invocation_execution_allowed": True,
            "adapter_invocation_execution_performed": True,
            "analytics_artifact_read_allowed": True,
            "analytics_artifact_read_performed": True,
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
            "certification_status": CERTIFICATION_STATUS,
        }

        return OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification(
            **body,
            execution_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_SCHEMA_VERSION",
    "CERTIFICATION_STATUS",
    "CERTIFIED_RESULT_TYPE",
    "EXPECTED_EXECUTION_STATUS",
    "EXPECTED_EXECUTION_RESULT_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError",
    "stable_hash",
]
