from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    CERTIFICATION_STATUS as OOP_016_CERTIFICATION_STATUS,
    CERTIFIED_RESULT_TYPE as OOP_016_CERTIFIED_RESULT_TYPE,
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
)

SCHEMA_VERSION = "OOP-017"
ENGINE_ID = "OOP-017"
POLICY_ID = (
    "oracle.operator.query-resolution-research-response-handoff-authorization-gate.v1"
)
HANDOFF_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-research-response-handoff-authorization.v1"
)
HANDOFF_STATUS = "operator_query_resolution_research_response_handoff_authorized"
HANDOFF_TYPE = "immutable_certified_query_result_to_research_response"

EXPECTED_CERTIFICATION_STATUS = OOP_016_CERTIFICATION_STATUS
EXPECTED_CERTIFIED_RESULT_TYPE = OOP_016_CERTIFIED_RESULT_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
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
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
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
class OracleOperatorQueryResolutionResearchResponseHandoffAuthorization:
    research_response_handoff_authorization_id: str
    source_execution_result_certification_id: str
    source_execution_result_certification_hash: str
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
    research_response_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    handoff_type: str
    certified_result_type: str
    read_adapter_contract_id: str
    execution_mode: str
    handoff_resolution_strategy: str
    handoff_entry_count: int
    handoff_response_artifact_entry_ids: tuple[str, ...]
    handoff_query_response_ids: tuple[str, ...]
    handoff_result_count: int
    handoff_result_hashes: tuple[str, ...]
    handoff_result_payloads: tuple[Mapping[str, Any], ...]
    certification_type_verified: bool
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    certified_result_type_verified: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    deterministic_handoff_verified: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
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
    handoff_status: str
    research_response_handoff_authorization_hash: str


class OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate:
    @staticmethod
    def _verify_certification(
        certification: OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "source must be the canonical OOP-016 result certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop("execution_result_certification_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification hash mismatch"
            )

        required_hashes = (
            certification.execution_result_certification_id,
            certification.source_adapter_invocation_execution_hash,
            certification.source_adapter_invocation_activation_hash,
            certification.source_adapter_execution_consumption_hash,
            certification.source_adapter_execution_authorization_hash,
            certification.source_adapter_execution_readiness_hash,
            certification.source_read_consumption_hash,
            certification.source_read_authorization_hash,
            certification.source_read_readiness_hash,
            certification.source_resolution_consumption_hash,
            certification.source_resolution_authorization_hash,
            certification.source_resolution_plan_hash,
            certification.source_query_admission_hash,
            certification.source_query_request_hash,
            certification.source_admission_hash,
            certification.source_dependency_receipt_hash,
            certification.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 lineage contains invalid hashes"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification is not active"
            )
        if certification.certified_result_type != EXPECTED_CERTIFIED_RESULT_TYPE:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified result type mismatch"
            )
        if certification.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if certification.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "query namespace mismatch"
            )

        if certification.certified_entry_count < 1:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certification contains no entries"
            )
        if certification.certified_entry_count != certification.certified_result_count:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified entry/result cardinality mismatch"
            )
        if certification.certified_result_count != len(
            certification.certified_result_payloads
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified payload cardinality mismatch"
            )
        if certification.certified_result_count != len(
            certification.certified_result_hashes
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified hash cardinality mismatch"
            )
        if certification.certified_entry_count != len(
            certification.certified_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified artifact-entry cardinality mismatch"
            )
        if certification.certified_entry_count != len(
            certification.certified_query_response_ids
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified query-response cardinality mismatch"
            )

        recomputed_hashes = tuple(
            stable_hash(item) for item in certification.certified_result_payloads
        )
        if recomputed_hashes != tuple(certification.certified_result_hashes):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified result payload hash mismatch"
            )

        required_truths = (
            certification.execution_type_verified,
            certification.execution_identity_verified,
            certification.execution_hash_verified,
            certification.execution_status_verified,
            certification.complete_lineage_verified,
            certification.namespaces_verified,
            certification.query_parameters_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.immutable_invocation_package_verified,
            certification.immutable_execution_package_verified,
            certification.execution_result_type_verified,
            certification.read_adapter_contract_verified,
            certification.bounded_artifact_read_verified,
            certification.single_read_invocation_verified,
            certification.execution_performed_verified,
            certification.artifact_read_performed_verified,
            certification.result_cardinality_verified,
            certification.result_identity_verified,
            certification.result_payload_hashes_verified,
            certification.deterministic_certification_verified,
            certification.adapter_invocation_execution_performed,
            certification.analytics_artifact_read_performed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification is incomplete"
            )

        forbidden_activity = (
            certification.analytics_query_execution_allowed,
            certification.analytics_query_execution_performed,
            certification.analytics_reexecution_allowed,
            certification.analytics_reexecution_performed,
            certification.analytics_database_connection_allowed,
            certification.analytics_database_connection_performed,
            certification.analytics_mutation_allowed,
            certification.analytics_mutation_performed,
            certification.research_response_materialization_allowed,
            certification.research_response_materialization_performed,
            certification.operator_session_construction_allowed,
            certification.operator_console_rendering_allowed,
            certification.operator_presentation_rendering_allowed,
            certification.publication_allowed,
            certification.publication_performed,
            certification.qseries_handoff_allowed,
            certification.qseries_execution_allowed,
            certification.qseries_execution_performed,
            certification.order_creation_allowed,
            certification.order_creation_performed,
            certification.funds_movement_allowed,
            certification.funds_movement_performed,
            certification.portfolio_mutation_allowed,
            certification.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification contains forbidden activity"
            )

    def authorize(
        self,
        *,
        certification: OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
    ) -> OracleOperatorQueryResolutionResearchResponseHandoffAuthorization:
        self._verify_certification(certification)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_result_certification_id": (
                    certification.execution_result_certification_id
                ),
                "source_execution_result_certification_hash": (
                    certification.execution_result_certification_hash
                ),
                "handoff_type": HANDOFF_TYPE,
                "research_response_namespace": EXPECTED_RESEARCH_RESPONSE_NAMESPACE,
                "certified_result_type": certification.certified_result_type,
                "handoff_response_artifact_entry_ids": (
                    certification.certified_response_artifact_entry_ids
                ),
                "handoff_query_response_ids": (
                    certification.certified_query_response_ids
                ),
                "handoff_result_hashes": certification.certified_result_hashes,
            }
        )

        body = {
            "research_response_handoff_authorization_id": authorization_id,
            "source_execution_result_certification_id": certification.execution_result_certification_id,
            "source_execution_result_certification_hash": certification.execution_result_certification_hash,
            "source_adapter_invocation_execution_id": certification.source_adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": certification.source_adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": certification.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": certification.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": certification.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": certification.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": certification.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": certification.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": certification.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": certification.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": certification.source_read_consumption_id,
            "source_read_consumption_hash": certification.source_read_consumption_hash,
            "source_read_authorization_id": certification.source_read_authorization_id,
            "source_read_authorization_hash": certification.source_read_authorization_hash,
            "source_read_readiness_id": certification.source_read_readiness_id,
            "source_read_readiness_hash": certification.source_read_readiness_hash,
            "source_resolution_consumption_id": certification.source_resolution_consumption_id,
            "source_resolution_consumption_hash": certification.source_resolution_consumption_hash,
            "source_resolution_authorization_id": certification.source_resolution_authorization_id,
            "source_resolution_authorization_hash": certification.source_resolution_authorization_hash,
            "source_resolution_plan_id": certification.source_resolution_plan_id,
            "source_resolution_plan_hash": certification.source_resolution_plan_hash,
            "source_query_admission_id": certification.source_query_admission_id,
            "source_query_admission_hash": certification.source_query_admission_hash,
            "source_query_request_id": certification.source_query_request_id,
            "source_query_request_hash": certification.source_query_request_hash,
            "source_admission_id": certification.source_admission_id,
            "source_admission_hash": certification.source_admission_hash,
            "source_dependency_receipt_id": certification.source_dependency_receipt_id,
            "source_dependency_receipt_hash": certification.source_dependency_receipt_hash,
            "source_authorization_id": certification.source_authorization_id,
            "source_authorization_hash": certification.source_authorization_hash,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": EXPECTED_RESEARCH_RESPONSE_NAMESPACE,
            "consumer_id": certification.consumer_id,
            "projection": certification.projection,
            "query_mode": certification.query_mode,
            "query_text": certification.query_text,
            "time_scope": certification.time_scope,
            "sort_order": certification.sort_order,
            "result_limit": certification.result_limit,
            "requested_tags": tuple(certification.requested_tags),
            "handoff_type": HANDOFF_TYPE,
            "certified_result_type": certification.certified_result_type,
            "read_adapter_contract_id": certification.read_adapter_contract_id,
            "execution_mode": certification.execution_mode,
            "handoff_resolution_strategy": certification.certified_resolution_strategy,
            "handoff_entry_count": certification.certified_entry_count,
            "handoff_response_artifact_entry_ids": tuple(
                certification.certified_response_artifact_entry_ids
            ),
            "handoff_query_response_ids": tuple(
                certification.certified_query_response_ids
            ),
            "handoff_result_count": certification.certified_result_count,
            "handoff_result_hashes": tuple(certification.certified_result_hashes),
            "handoff_result_payloads": tuple(certification.certified_result_payloads),
            "certification_type_verified": True,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "certified_result_type_verified": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "deterministic_handoff_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": False,
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
            "handoff_status": HANDOFF_STATUS,
        }

        return OracleOperatorQueryResolutionResearchResponseHandoffAuthorization(
            **body,
            research_response_handoff_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "HANDOFF_SCHEMA_VERSION",
    "HANDOFF_STATUS",
    "HANDOFF_TYPE",
    "EXPECTED_CERTIFICATION_STATUS",
    "EXPECTED_CERTIFIED_RESULT_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "EXPECTED_RESEARCH_RESPONSE_NAMESPACE",
    "OracleOperatorQueryResolutionResearchResponseHandoffAuthorization",
    "OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate",
    "OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError",
    "stable_hash",
]
