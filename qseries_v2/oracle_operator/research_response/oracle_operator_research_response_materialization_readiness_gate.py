from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_handoff_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_018_CONSUMPTION_STATUS,
    RESPONSE_INPUT_PACKAGE_TYPE as OOP_018_RESPONSE_INPUT_PACKAGE_TYPE,
    OracleOperatorResearchResponseHandoffAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-019"
ENGINE_ID = "OOP-019"
POLICY_ID = "oracle.operator.research-response-materialization-readiness-gate.v1"
READINESS_SCHEMA_VERSION = (
    "oracle.operator.research-response.materialization-readiness.v1"
)
READINESS_STATUS = "operator_research_response_materialization_ready"
READINESS_TYPE = "immutable_research_response_materialization_readiness"

EXPECTED_CONSUMPTION_STATUS = OOP_018_CONSUMPTION_STATUS
EXPECTED_RESPONSE_INPUT_PACKAGE_TYPE = OOP_018_RESPONSE_INPUT_PACKAGE_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorResearchResponseMaterializationReadinessInvariantError(
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
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
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
class OracleOperatorResearchResponseMaterializationReadiness:
    research_response_materialization_readiness_id: str
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
    certified_result_type: str
    read_adapter_contract_id: str
    execution_mode: str
    response_resolution_strategy: str
    response_entry_count: int
    response_artifact_entry_ids: tuple[str, ...]
    response_query_response_ids: tuple[str, ...]
    response_result_count: int
    response_result_hashes: tuple[str, ...]
    response_result_payloads: tuple[Mapping[str, Any], ...]
    consumption_type_verified: bool
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    response_input_package_verified: bool
    response_schema_inputs_verified: bool
    response_content_inputs_verified: bool
    deterministic_readiness_verified: bool
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
    readiness_status: str
    research_response_materialization_readiness_hash: str


class OracleOperatorResearchResponseMaterializationReadinessGate:
    @staticmethod
    def _verify_consumption(
        consumption: OracleOperatorResearchResponseHandoffAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorResearchResponseHandoffAuthorizationConsumption,
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "source must be the canonical OOP-018 handoff consumption"
            )

        body = asdict(consumption)
        supplied_hash = body.pop("research_response_handoff_consumption_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption hash mismatch"
            )

        required_hashes = (
            consumption.research_response_handoff_consumption_id,
            consumption.source_research_response_handoff_authorization_hash,
            consumption.source_execution_result_certification_hash,
            consumption.source_adapter_invocation_execution_hash,
            consumption.source_adapter_invocation_activation_hash,
            consumption.source_adapter_execution_consumption_hash,
            consumption.source_adapter_execution_authorization_hash,
            consumption.source_adapter_execution_readiness_hash,
            consumption.source_read_consumption_hash,
            consumption.source_read_authorization_hash,
            consumption.source_read_readiness_hash,
            consumption.source_resolution_consumption_hash,
            consumption.source_resolution_authorization_hash,
            consumption.source_resolution_plan_hash,
            consumption.source_query_admission_hash,
            consumption.source_query_request_hash,
            consumption.source_admission_hash,
            consumption.source_dependency_receipt_hash,
            consumption.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 lineage contains invalid hashes"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 handoff consumption is not complete"
            )
        if (
            consumption.response_input_package_type
            != EXPECTED_RESPONSE_INPUT_PACKAGE_TYPE
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "response input package type mismatch"
            )
        if consumption.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "operator namespace mismatch"
            )
        if consumption.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "query namespace mismatch"
            )
        if (
            consumption.research_response_namespace
            != EXPECTED_RESEARCH_RESPONSE_NAMESPACE
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "research response namespace mismatch"
            )

        if consumption.consumed_entry_count < 1:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumption contains no entries"
            )
        if consumption.consumed_entry_count != consumption.consumed_result_count:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed entry/result cardinality mismatch"
            )
        if consumption.consumed_result_count != len(
            consumption.consumed_result_payloads
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed payload cardinality mismatch"
            )
        if consumption.consumed_result_count != len(
            consumption.consumed_result_hashes
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed hash cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_response_artifact_entry_ids
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed artifact-entry cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_query_response_ids
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed query-response cardinality mismatch"
            )

        recomputed_hashes = tuple(
            stable_hash(item) for item in consumption.consumed_result_payloads
        )
        if recomputed_hashes != tuple(consumption.consumed_result_hashes):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed payload hash mismatch"
            )

        for index, payload in enumerate(consumption.consumed_result_payloads):
            if not isinstance(payload, Mapping):
                raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                    "consumed result payload must be a mapping"
                )
            if (
                payload.get("response_artifact_entry_id")
                != consumption.consumed_response_artifact_entry_ids[index]
            ):
                raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                    "consumed artifact-entry identity mismatch"
                )
            if (
                payload.get("query_response_id")
                != consumption.consumed_query_response_ids[index]
            ):
                raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                    "consumed query-response identity mismatch"
                )

        required_truths = (
            consumption.handoff_type_verified,
            consumption.handoff_identity_verified,
            consumption.handoff_hash_verified,
            consumption.handoff_status_verified,
            consumption.complete_lineage_verified,
            consumption.namespaces_verified,
            consumption.query_parameters_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.result_cardinality_verified,
            consumption.result_identity_verified,
            consumption.result_payload_hashes_verified,
            consumption.single_use_consumption_verified,
            consumption.deterministic_consumption_verified,
            consumption.query_subsystem_complete,
            consumption.research_response_handoff_ready,
            consumption.research_response_handoff_authorized,
            consumption.research_response_handoff_consumed,
        )
        if not all(required_truths):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption is incomplete"
            )

        forbidden_activity = (
            consumption.research_response_materialization_ready,
            consumption.research_response_materialization_allowed,
            consumption.research_response_materialization_performed,
            consumption.operator_session_construction_allowed,
            consumption.operator_console_rendering_allowed,
            consumption.operator_presentation_rendering_allowed,
            consumption.publication_allowed,
            consumption.publication_performed,
            consumption.qseries_handoff_allowed,
            consumption.qseries_execution_allowed,
            consumption.qseries_execution_performed,
            consumption.order_creation_allowed,
            consumption.order_creation_performed,
            consumption.funds_movement_allowed,
            consumption.funds_movement_performed,
            consumption.portfolio_mutation_allowed,
            consumption.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption contains forbidden downstream activity"
            )

    def evaluate(
        self,
        *,
        consumption: OracleOperatorResearchResponseHandoffAuthorizationConsumption,
    ) -> OracleOperatorResearchResponseMaterializationReadiness:
        self._verify_consumption(consumption)

        readiness_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_research_response_handoff_consumption_id": (
                    consumption.research_response_handoff_consumption_id
                ),
                "source_research_response_handoff_consumption_hash": (
                    consumption.research_response_handoff_consumption_hash
                ),
                "readiness_type": READINESS_TYPE,
                "response_input_package_type": consumption.response_input_package_type,
                "response_artifact_entry_ids": (
                    consumption.consumed_response_artifact_entry_ids
                ),
                "response_query_response_ids": (
                    consumption.consumed_query_response_ids
                ),
                "response_result_hashes": consumption.consumed_result_hashes,
            }
        )

        body = {
            "research_response_materialization_readiness_id": readiness_id,
            "source_research_response_handoff_consumption_id": consumption.research_response_handoff_consumption_id,
            "source_research_response_handoff_consumption_hash": consumption.research_response_handoff_consumption_hash,
            "source_research_response_handoff_authorization_id": consumption.source_research_response_handoff_authorization_id,
            "source_research_response_handoff_authorization_hash": consumption.source_research_response_handoff_authorization_hash,
            "source_execution_result_certification_id": consumption.source_execution_result_certification_id,
            "source_execution_result_certification_hash": consumption.source_execution_result_certification_hash,
            "source_adapter_invocation_execution_id": consumption.source_adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": consumption.source_adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": consumption.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": consumption.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": consumption.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": consumption.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": consumption.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": consumption.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": consumption.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": consumption.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": consumption.source_read_consumption_id,
            "source_read_consumption_hash": consumption.source_read_consumption_hash,
            "source_read_authorization_id": consumption.source_read_authorization_id,
            "source_read_authorization_hash": consumption.source_read_authorization_hash,
            "source_read_readiness_id": consumption.source_read_readiness_id,
            "source_read_readiness_hash": consumption.source_read_readiness_hash,
            "source_resolution_consumption_id": consumption.source_resolution_consumption_id,
            "source_resolution_consumption_hash": consumption.source_resolution_consumption_hash,
            "source_resolution_authorization_id": consumption.source_resolution_authorization_id,
            "source_resolution_authorization_hash": consumption.source_resolution_authorization_hash,
            "source_resolution_plan_id": consumption.source_resolution_plan_id,
            "source_resolution_plan_hash": consumption.source_resolution_plan_hash,
            "source_query_admission_id": consumption.source_query_admission_id,
            "source_query_admission_hash": consumption.source_query_admission_hash,
            "source_query_request_id": consumption.source_query_request_id,
            "source_query_request_hash": consumption.source_query_request_hash,
            "source_admission_id": consumption.source_admission_id,
            "source_admission_hash": consumption.source_admission_hash,
            "source_dependency_receipt_id": consumption.source_dependency_receipt_id,
            "source_dependency_receipt_hash": consumption.source_dependency_receipt_hash,
            "source_authorization_id": consumption.source_authorization_id,
            "source_authorization_hash": consumption.source_authorization_hash,
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "research_response_namespace": consumption.research_response_namespace,
            "consumer_id": consumption.consumer_id,
            "projection": consumption.projection,
            "query_mode": consumption.query_mode,
            "query_text": consumption.query_text,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "response_input_package_type": consumption.response_input_package_type,
            "readiness_type": READINESS_TYPE,
            "certified_result_type": consumption.certified_result_type,
            "read_adapter_contract_id": consumption.read_adapter_contract_id,
            "execution_mode": consumption.execution_mode,
            "response_resolution_strategy": consumption.consumed_resolution_strategy,
            "response_entry_count": consumption.consumed_entry_count,
            "response_artifact_entry_ids": tuple(
                consumption.consumed_response_artifact_entry_ids
            ),
            "response_query_response_ids": tuple(
                consumption.consumed_query_response_ids
            ),
            "response_result_count": consumption.consumed_result_count,
            "response_result_hashes": tuple(consumption.consumed_result_hashes),
            "response_result_payloads": tuple(consumption.consumed_result_payloads),
            "consumption_type_verified": True,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "response_input_package_verified": True,
            "response_schema_inputs_verified": True,
            "response_content_inputs_verified": True,
            "deterministic_readiness_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": True,
            "research_response_materialization_ready": True,
            "research_response_materialization_authorized": False,
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
            "readiness_status": READINESS_STATUS,
        }

        return OracleOperatorResearchResponseMaterializationReadiness(
            **body,
            research_response_materialization_readiness_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "READINESS_SCHEMA_VERSION",
    "READINESS_STATUS",
    "READINESS_TYPE",
    "EXPECTED_CONSUMPTION_STATUS",
    "EXPECTED_RESPONSE_INPUT_PACKAGE_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "EXPECTED_RESEARCH_RESPONSE_NAMESPACE",
    "OracleOperatorResearchResponseMaterializationReadiness",
    "OracleOperatorResearchResponseMaterializationReadinessGate",
    "OracleOperatorResearchResponseMaterializationReadinessInvariantError",
    "stable_hash",
]
