from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_research_response_handoff_authorization_gate import (
    HANDOFF_STATUS as OOP_017_HANDOFF_STATUS,
    HANDOFF_TYPE as OOP_017_HANDOFF_TYPE,
    OracleOperatorQueryResolutionResearchResponseHandoffAuthorization,
)

SCHEMA_VERSION = "OOP-018"
ENGINE_ID = "OOP-018"
POLICY_ID = (
    "oracle.operator.research-response-handoff-authorization-consumption-gate.v1"
)
CONSUMPTION_SCHEMA_VERSION = (
    "oracle.operator.research-response.handoff-authorization-consumption.v1"
)
CONSUMPTION_STATUS = "operator_research_response_handoff_authorization_consumed"
RESPONSE_INPUT_PACKAGE_TYPE = (
    "single_use_immutable_certified_research_response_input_package"
)

EXPECTED_HANDOFF_STATUS = OOP_017_HANDOFF_STATUS
EXPECTED_HANDOFF_TYPE = OOP_017_HANDOFF_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
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
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
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
class OracleOperatorResearchResponseHandoffAuthorizationConsumption:
    research_response_handoff_consumption_id: str
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
    handoff_type: str
    response_input_package_type: str
    certified_result_type: str
    read_adapter_contract_id: str
    execution_mode: str
    consumed_resolution_strategy: str
    consumed_entry_count: int
    consumed_response_artifact_entry_ids: tuple[str, ...]
    consumed_query_response_ids: tuple[str, ...]
    consumed_result_count: int
    consumed_result_hashes: tuple[str, ...]
    consumed_result_payloads: tuple[Mapping[str, Any], ...]
    handoff_type_verified: bool
    handoff_identity_verified: bool
    handoff_hash_verified: bool
    handoff_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    single_use_consumption_verified: bool
    deterministic_consumption_verified: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
    research_response_materialization_ready: bool
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
    consumption_status: str
    research_response_handoff_consumption_hash: str


class OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate:
    @staticmethod
    def _verify_authorization(
        authorization: OracleOperatorQueryResolutionResearchResponseHandoffAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            OracleOperatorQueryResolutionResearchResponseHandoffAuthorization,
        ):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "source must be the canonical OOP-017 handoff authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop("research_response_handoff_authorization_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "OOP-017 handoff authorization hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "OOP-017 handoff authorization hash mismatch"
            )

        required_hashes = (
            authorization.research_response_handoff_authorization_id,
            authorization.source_execution_result_certification_hash,
            authorization.source_adapter_invocation_execution_hash,
            authorization.source_adapter_invocation_activation_hash,
            authorization.source_adapter_execution_consumption_hash,
            authorization.source_adapter_execution_authorization_hash,
            authorization.source_adapter_execution_readiness_hash,
            authorization.source_read_consumption_hash,
            authorization.source_read_authorization_hash,
            authorization.source_read_readiness_hash,
            authorization.source_resolution_consumption_hash,
            authorization.source_resolution_authorization_hash,
            authorization.source_resolution_plan_hash,
            authorization.source_query_admission_hash,
            authorization.source_query_request_hash,
            authorization.source_admission_hash,
            authorization.source_dependency_receipt_hash,
            authorization.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "OOP-017 lineage contains invalid hashes"
            )

        if authorization.handoff_status != EXPECTED_HANDOFF_STATUS:
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "OOP-017 handoff authorization is not active"
            )
        if authorization.handoff_type != EXPECTED_HANDOFF_TYPE:
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "handoff type mismatch"
            )
        if authorization.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "operator namespace mismatch"
            )
        if authorization.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "query namespace mismatch"
            )
        if (
            authorization.research_response_namespace
            != EXPECTED_RESEARCH_RESPONSE_NAMESPACE
        ):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "research response namespace mismatch"
            )

        if authorization.handoff_entry_count < 1:
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "handoff contains no entries"
            )
        if authorization.handoff_entry_count != authorization.handoff_result_count:
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "handoff entry/result cardinality mismatch"
            )
        if authorization.handoff_result_count != len(
            authorization.handoff_result_payloads
        ):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "handoff payload cardinality mismatch"
            )
        if authorization.handoff_result_count != len(
            authorization.handoff_result_hashes
        ):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "handoff hash cardinality mismatch"
            )

        recomputed_hashes = tuple(
            stable_hash(item) for item in authorization.handoff_result_payloads
        )
        if recomputed_hashes != tuple(authorization.handoff_result_hashes):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "handoff result payload hash mismatch"
            )

        required_truths = (
            authorization.certification_type_verified,
            authorization.certification_identity_verified,
            authorization.certification_hash_verified,
            authorization.certification_status_verified,
            authorization.complete_lineage_verified,
            authorization.namespaces_verified,
            authorization.query_parameters_verified,
            authorization.frozen_scope_verified,
            authorization.frozen_scope_preserved,
            authorization.certified_result_type_verified,
            authorization.result_cardinality_verified,
            authorization.result_identity_verified,
            authorization.result_payload_hashes_verified,
            authorization.deterministic_handoff_verified,
            authorization.query_subsystem_complete,
            authorization.research_response_handoff_ready,
            authorization.research_response_handoff_authorized,
        )
        if not all(required_truths):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "OOP-017 handoff authorization is incomplete"
            )

        forbidden_activity = (
            authorization.research_response_handoff_consumed,
            authorization.research_response_materialization_allowed,
            authorization.research_response_materialization_performed,
            authorization.operator_session_construction_allowed,
            authorization.operator_console_rendering_allowed,
            authorization.operator_presentation_rendering_allowed,
            authorization.publication_allowed,
            authorization.publication_performed,
            authorization.qseries_handoff_allowed,
            authorization.qseries_execution_allowed,
            authorization.qseries_execution_performed,
            authorization.order_creation_allowed,
            authorization.order_creation_performed,
            authorization.funds_movement_allowed,
            authorization.funds_movement_performed,
            authorization.portfolio_mutation_allowed,
            authorization.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError(
                "OOP-017 authorization contains forbidden downstream activity"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorQueryResolutionResearchResponseHandoffAuthorization,
    ) -> OracleOperatorResearchResponseHandoffAuthorizationConsumption:
        self._verify_authorization(authorization)

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_research_response_handoff_authorization_id": (
                    authorization.research_response_handoff_authorization_id
                ),
                "source_research_response_handoff_authorization_hash": (
                    authorization.research_response_handoff_authorization_hash
                ),
                "response_input_package_type": RESPONSE_INPUT_PACKAGE_TYPE,
                "research_response_namespace": (
                    authorization.research_response_namespace
                ),
                "consumed_response_artifact_entry_ids": (
                    authorization.handoff_response_artifact_entry_ids
                ),
                "consumed_query_response_ids": (
                    authorization.handoff_query_response_ids
                ),
                "consumed_result_hashes": authorization.handoff_result_hashes,
            }
        )

        body = {
            "research_response_handoff_consumption_id": consumption_id,
            "source_research_response_handoff_authorization_id": authorization.research_response_handoff_authorization_id,
            "source_research_response_handoff_authorization_hash": authorization.research_response_handoff_authorization_hash,
            "source_execution_result_certification_id": authorization.source_execution_result_certification_id,
            "source_execution_result_certification_hash": authorization.source_execution_result_certification_hash,
            "source_adapter_invocation_execution_id": authorization.source_adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": authorization.source_adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": authorization.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": authorization.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": authorization.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": authorization.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": authorization.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": authorization.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": authorization.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": authorization.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": authorization.source_read_consumption_id,
            "source_read_consumption_hash": authorization.source_read_consumption_hash,
            "source_read_authorization_id": authorization.source_read_authorization_id,
            "source_read_authorization_hash": authorization.source_read_authorization_hash,
            "source_read_readiness_id": authorization.source_read_readiness_id,
            "source_read_readiness_hash": authorization.source_read_readiness_hash,
            "source_resolution_consumption_id": authorization.source_resolution_consumption_id,
            "source_resolution_consumption_hash": authorization.source_resolution_consumption_hash,
            "source_resolution_authorization_id": authorization.source_resolution_authorization_id,
            "source_resolution_authorization_hash": authorization.source_resolution_authorization_hash,
            "source_resolution_plan_id": authorization.source_resolution_plan_id,
            "source_resolution_plan_hash": authorization.source_resolution_plan_hash,
            "source_query_admission_id": authorization.source_query_admission_id,
            "source_query_admission_hash": authorization.source_query_admission_hash,
            "source_query_request_id": authorization.source_query_request_id,
            "source_query_request_hash": authorization.source_query_request_hash,
            "source_admission_id": authorization.source_admission_id,
            "source_admission_hash": authorization.source_admission_hash,
            "source_dependency_receipt_id": authorization.source_dependency_receipt_id,
            "source_dependency_receipt_hash": authorization.source_dependency_receipt_hash,
            "source_authorization_id": authorization.source_authorization_id,
            "source_authorization_hash": authorization.source_authorization_hash,
            "operator_namespace": authorization.operator_namespace,
            "query_namespace": authorization.query_namespace,
            "research_response_namespace": authorization.research_response_namespace,
            "consumer_id": authorization.consumer_id,
            "projection": authorization.projection,
            "query_mode": authorization.query_mode,
            "query_text": authorization.query_text,
            "time_scope": authorization.time_scope,
            "sort_order": authorization.sort_order,
            "result_limit": authorization.result_limit,
            "requested_tags": tuple(authorization.requested_tags),
            "handoff_type": authorization.handoff_type,
            "response_input_package_type": RESPONSE_INPUT_PACKAGE_TYPE,
            "certified_result_type": authorization.certified_result_type,
            "read_adapter_contract_id": authorization.read_adapter_contract_id,
            "execution_mode": authorization.execution_mode,
            "consumed_resolution_strategy": authorization.handoff_resolution_strategy,
            "consumed_entry_count": authorization.handoff_entry_count,
            "consumed_response_artifact_entry_ids": tuple(
                authorization.handoff_response_artifact_entry_ids
            ),
            "consumed_query_response_ids": tuple(
                authorization.handoff_query_response_ids
            ),
            "consumed_result_count": authorization.handoff_result_count,
            "consumed_result_hashes": tuple(authorization.handoff_result_hashes),
            "consumed_result_payloads": tuple(authorization.handoff_result_payloads),
            "handoff_type_verified": True,
            "handoff_identity_verified": True,
            "handoff_hash_verified": True,
            "handoff_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "single_use_consumption_verified": True,
            "deterministic_consumption_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": True,
            "research_response_materialization_ready": False,
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
            "consumption_status": CONSUMPTION_STATUS,
        }

        return OracleOperatorResearchResponseHandoffAuthorizationConsumption(
            **body,
            research_response_handoff_consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_SCHEMA_VERSION",
    "CONSUMPTION_STATUS",
    "RESPONSE_INPUT_PACKAGE_TYPE",
    "EXPECTED_HANDOFF_STATUS",
    "EXPECTED_HANDOFF_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "EXPECTED_RESEARCH_RESPONSE_NAMESPACE",
    "OracleOperatorResearchResponseHandoffAuthorizationConsumption",
    "OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate",
    "OracleOperatorResearchResponseHandoffAuthorizationConsumptionInvariantError",
    "stable_hash",
]
