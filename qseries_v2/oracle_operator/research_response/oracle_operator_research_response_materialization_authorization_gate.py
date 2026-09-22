from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_readiness_gate import (
    READINESS_STATUS as OOP_019_READINESS_STATUS,
    READINESS_TYPE as OOP_019_READINESS_TYPE,
    OracleOperatorResearchResponseMaterializationReadiness,
)

SCHEMA_VERSION = "OOP-020"
ENGINE_ID = "OOP-020"
POLICY_ID = "oracle.operator.research-response-materialization-authorization-gate.v1"
AUTHORIZATION_SCHEMA_VERSION = (
    "oracle.operator.research-response.materialization-authorization.v1"
)
AUTHORIZATION_STATUS = "operator_research_response_materialization_authorized"
AUTHORIZATION_TYPE = "single_use_immutable_research_response_materialization_authorization"

EXPECTED_READINESS_STATUS = OOP_019_READINESS_STATUS
EXPECTED_READINESS_TYPE = OOP_019_READINESS_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
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
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
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
class OracleOperatorResearchResponseMaterializationAuthorization:
    research_response_materialization_authorization_id: str
    source_research_response_materialization_readiness_id: str
    source_research_response_materialization_readiness_hash: str
    source_research_response_handoff_consumption_id: str
    source_research_response_handoff_consumption_hash: str
    source_research_response_handoff_authorization_id: str
    source_research_response_handoff_authorization_hash: str
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
    response_input_package_type: str
    readiness_type: str
    authorization_type: str
    certified_result_type: str
    read_adapter_contract_id: str
    execution_mode: str
    authorized_resolution_strategy: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    authorized_result_count: int
    authorized_result_hashes: tuple[str, ...]
    authorized_result_payloads: tuple[Mapping[str, Any], ...]
    readiness_type_verified: bool
    readiness_identity_verified: bool
    readiness_hash_verified: bool
    readiness_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    response_input_package_verified: bool
    response_schema_inputs_verified: bool
    response_content_inputs_verified: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    single_use_authorization_verified: bool
    deterministic_authorization_verified: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
    research_response_materialization_ready: bool
    research_response_materialization_authorized: bool
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
    research_response_materialization_authorization_hash: str


class OracleOperatorResearchResponseMaterializationAuthorizationGate:
    @staticmethod
    def _verify_readiness(
        readiness: OracleOperatorResearchResponseMaterializationReadiness,
    ) -> None:
        if not isinstance(
            readiness,
            OracleOperatorResearchResponseMaterializationReadiness,
        ):
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "source must be the canonical OOP-019 materialization readiness"
            )

        body = asdict(readiness)
        supplied_hash = body.pop(
            "research_response_materialization_readiness_hash",
            None,
        )
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "OOP-019 readiness hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "OOP-019 readiness hash mismatch"
            )

        required_hashes = (
            readiness.research_response_materialization_readiness_id,
            readiness.source_research_response_handoff_consumption_hash,
            readiness.source_research_response_handoff_authorization_hash,
            readiness.source_execution_result_certification_hash,
            readiness.source_adapter_invocation_execution_hash,
            readiness.source_adapter_invocation_activation_hash,
            readiness.source_adapter_execution_consumption_hash,
            readiness.source_adapter_execution_authorization_hash,
            readiness.source_adapter_execution_readiness_hash,
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
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "OOP-019 lineage contains invalid hashes"
            )

        if readiness.readiness_status != EXPECTED_READINESS_STATUS:
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "OOP-019 readiness is not active"
            )
        if readiness.readiness_type != EXPECTED_READINESS_TYPE:
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "readiness type mismatch"
            )
        if readiness.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if readiness.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "query namespace mismatch"
            )
        if (
            readiness.research_response_namespace
            != EXPECTED_RESEARCH_RESPONSE_NAMESPACE
        ):
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "research response namespace mismatch"
            )

        if readiness.response_entry_count < 1:
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "readiness contains no response entries"
            )
        if readiness.response_entry_count != readiness.response_result_count:
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "response entry/result cardinality mismatch"
            )
        if readiness.response_result_count != len(readiness.response_result_payloads):
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "response payload cardinality mismatch"
            )
        if readiness.response_result_count != len(readiness.response_result_hashes):
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "response hash cardinality mismatch"
            )

        recomputed_hashes = tuple(
            stable_hash(item) for item in readiness.response_result_payloads
        )
        if recomputed_hashes != tuple(readiness.response_result_hashes):
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "response payload hash mismatch"
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
            readiness.result_cardinality_verified,
            readiness.result_identity_verified,
            readiness.result_payload_hashes_verified,
            readiness.response_input_package_verified,
            readiness.response_schema_inputs_verified,
            readiness.response_content_inputs_verified,
            readiness.deterministic_readiness_verified,
            readiness.query_subsystem_complete,
            readiness.research_response_handoff_ready,
            readiness.research_response_handoff_authorized,
            readiness.research_response_handoff_consumed,
            readiness.research_response_materialization_ready,
        )
        if not all(required_truths):
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "OOP-019 readiness is incomplete"
            )

        forbidden_activity = (
            readiness.research_response_materialization_authorized,
            readiness.research_response_materialization_allowed,
            readiness.research_response_materialization_performed,
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
            raise OracleOperatorResearchResponseMaterializationAuthorizationInvariantError(
                "OOP-019 readiness contains forbidden downstream activity"
            )

    def authorize(
        self,
        *,
        readiness: OracleOperatorResearchResponseMaterializationReadiness,
    ) -> OracleOperatorResearchResponseMaterializationAuthorization:
        self._verify_readiness(readiness)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_research_response_materialization_readiness_id": (
                    readiness.research_response_materialization_readiness_id
                ),
                "source_research_response_materialization_readiness_hash": (
                    readiness.research_response_materialization_readiness_hash
                ),
                "authorization_type": AUTHORIZATION_TYPE,
                "response_input_package_type": readiness.response_input_package_type,
                "authorized_response_artifact_entry_ids": (
                    readiness.response_artifact_entry_ids
                ),
                "authorized_query_response_ids": (
                    readiness.response_query_response_ids
                ),
                "authorized_result_hashes": readiness.response_result_hashes,
            }
        )

        body = {
            "research_response_materialization_authorization_id": authorization_id,
            "source_research_response_materialization_readiness_id": readiness.research_response_materialization_readiness_id,
            "source_research_response_materialization_readiness_hash": readiness.research_response_materialization_readiness_hash,
            "source_research_response_handoff_consumption_id": readiness.source_research_response_handoff_consumption_id,
            "source_research_response_handoff_consumption_hash": readiness.source_research_response_handoff_consumption_hash,
            "source_research_response_handoff_authorization_id": readiness.source_research_response_handoff_authorization_id,
            "source_research_response_handoff_authorization_hash": readiness.source_research_response_handoff_authorization_hash,
            "source_execution_result_certification_id": readiness.source_execution_result_certification_id,
            "source_execution_result_certification_hash": readiness.source_execution_result_certification_hash,
            "source_adapter_invocation_execution_id": readiness.source_adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": readiness.source_adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": readiness.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": readiness.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": readiness.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": readiness.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": readiness.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": readiness.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": readiness.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": readiness.source_adapter_execution_readiness_hash,
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
            "research_response_namespace": readiness.research_response_namespace,
            "consumer_id": readiness.consumer_id,
            "projection": readiness.projection,
            "query_mode": readiness.query_mode,
            "query_text": readiness.query_text,
            "time_scope": readiness.time_scope,
            "sort_order": readiness.sort_order,
            "result_limit": readiness.result_limit,
            "requested_tags": tuple(readiness.requested_tags),
            "response_input_package_type": readiness.response_input_package_type,
            "readiness_type": readiness.readiness_type,
            "authorization_type": AUTHORIZATION_TYPE,
            "certified_result_type": readiness.certified_result_type,
            "read_adapter_contract_id": readiness.read_adapter_contract_id,
            "execution_mode": readiness.execution_mode,
            "authorized_resolution_strategy": readiness.response_resolution_strategy,
            "authorized_entry_count": readiness.response_entry_count,
            "authorized_response_artifact_entry_ids": tuple(
                readiness.response_artifact_entry_ids
            ),
            "authorized_query_response_ids": tuple(
                readiness.response_query_response_ids
            ),
            "authorized_result_count": readiness.response_result_count,
            "authorized_result_hashes": tuple(readiness.response_result_hashes),
            "authorized_result_payloads": tuple(readiness.response_result_payloads),
            "readiness_type_verified": True,
            "readiness_identity_verified": True,
            "readiness_hash_verified": True,
            "readiness_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "response_input_package_verified": True,
            "response_schema_inputs_verified": True,
            "response_content_inputs_verified": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "single_use_authorization_verified": True,
            "deterministic_authorization_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": True,
            "research_response_materialization_ready": True,
            "research_response_materialization_authorized": True,
            "research_response_materialization_allowed": True,
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

        return OracleOperatorResearchResponseMaterializationAuthorization(
            **body,
            research_response_materialization_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "AUTHORIZATION_TYPE",
    "EXPECTED_READINESS_STATUS",
    "EXPECTED_READINESS_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "EXPECTED_RESEARCH_RESPONSE_NAMESPACE",
    "OracleOperatorResearchResponseMaterializationAuthorization",
    "OracleOperatorResearchResponseMaterializationAuthorizationGate",
    "OracleOperatorResearchResponseMaterializationAuthorizationInvariantError",
    "stable_hash",
]
