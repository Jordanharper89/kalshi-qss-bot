from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_013_CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE as OOP_013_EXECUTION_PACKAGE_TYPE,
    OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-014"
ENGINE_ID = "OOP-014"
POLICY_ID = "oracle.operator.query-resolution-adapter-invocation-activation-gate.v1"
ACTIVATION_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-adapter-invocation-activation.v1"
)
ACTIVATION_STATUS = "operator_query_resolution_adapter_invocation_active"
ACTIVE_INVOCATION_TYPE = "single_active_bounded_read_only_adapter_invocation"

EXPECTED_CONSUMPTION_STATUS = OOP_013_CONSUMPTION_STATUS
EXPECTED_EXECUTION_PACKAGE_TYPE = OOP_013_EXECUTION_PACKAGE_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
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
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
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
class OracleOperatorQueryResolutionAdapterInvocationActivation:
    adapter_invocation_activation_id: str
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
    read_invocation_mode: str
    read_adapter_contract_id: str
    execution_mode: str
    active_resolution_strategy: str
    active_entry_count: int
    active_response_artifact_entry_ids: tuple[str, ...]
    active_query_response_ids: tuple[str, ...]
    consumption_type_verified: bool
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_invocation_package_verified: bool
    immutable_execution_package_verified: bool
    read_adapter_contract_verified: bool
    bounded_artifact_read_verified: bool
    single_read_invocation_verified: bool
    single_use_execution_consumption_verified: bool
    deterministic_activation_verified: bool
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
    activation_status: str
    adapter_invocation_activation_hash: str


class OracleOperatorQueryResolutionAdapterInvocationActivationGate:
    @staticmethod
    def _verify_consumption(
        consumption: OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumption,
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "source must be the canonical OOP-013 execution consumption record"
            )

        body = asdict(consumption)
        supplied_hash = body.pop("adapter_execution_consumption_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "OOP-013 consumption hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "OOP-013 consumption hash mismatch"
            )

        required_hashes = (
            consumption.adapter_execution_consumption_id,
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
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "OOP-013 lineage contains invalid hashes"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "OOP-013 consumption is not active"
            )
        if consumption.execution_package_type != EXPECTED_EXECUTION_PACKAGE_TYPE:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "execution package type mismatch"
            )
        if consumption.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "operator namespace mismatch"
            )
        if consumption.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "query namespace mismatch"
            )

        if consumption.consumed_entry_count < 1:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "consumption contains no entries"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_query_response_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(consumption.consumed_response_artifact_entry_ids)) != consumption.consumed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(consumption.consumed_query_response_ids)) != consumption.consumed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            consumption.authorization_type_verified,
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_status_verified,
            consumption.complete_lineage_verified,
            consumption.namespaces_verified,
            consumption.query_parameters_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.immutable_invocation_package_verified,
            consumption.immutable_execution_package_verified,
            consumption.read_adapter_contract_verified,
            consumption.bounded_artifact_read_verified,
            consumption.single_read_invocation_verified,
            consumption.single_use_execution_consumption_verified,
            consumption.deterministic_consumption_verified,
            consumption.adapter_invocation_execution_ready,
            consumption.adapter_invocation_execution_authorized,
            consumption.adapter_invocation_execution_allowed,
            consumption.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "OOP-013 consumption is incomplete"
            )

        forbidden_activity = (
            consumption.adapter_invocation_execution_performed,
            consumption.analytics_artifact_read_performed,
            consumption.analytics_query_execution_allowed,
            consumption.analytics_query_execution_performed,
            consumption.analytics_reexecution_allowed,
            consumption.analytics_reexecution_performed,
            consumption.analytics_database_connection_allowed,
            consumption.analytics_database_connection_performed,
            consumption.analytics_mutation_allowed,
            consumption.analytics_mutation_performed,
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
            raise OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError(
                "OOP-013 consumption contains forbidden activity"
            )

    def activate(
        self,
        *,
        consumption: OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumption,
    ) -> OracleOperatorQueryResolutionAdapterInvocationActivation:
        self._verify_consumption(consumption)

        adapter_invocation_activation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_adapter_execution_consumption_id": (
                    consumption.adapter_execution_consumption_id
                ),
                "source_adapter_execution_consumption_hash": (
                    consumption.adapter_execution_consumption_hash
                ),
                "active_invocation_type": ACTIVE_INVOCATION_TYPE,
                "execution_package_type": consumption.execution_package_type,
                "execution_mode": consumption.execution_mode,
                "read_adapter_contract_id": consumption.read_adapter_contract_id,
                "active_resolution_strategy": consumption.consumed_resolution_strategy,
                "query_mode": consumption.query_mode,
                "query_text": consumption.query_text,
                "time_scope": consumption.time_scope,
                "sort_order": consumption.sort_order,
                "result_limit": consumption.result_limit,
                "requested_tags": consumption.requested_tags,
                "active_response_artifact_entry_ids": (
                    consumption.consumed_response_artifact_entry_ids
                ),
                "active_query_response_ids": (
                    consumption.consumed_query_response_ids
                ),
            }
        )

        body = {
            "adapter_invocation_activation_id": adapter_invocation_activation_id,
            "source_adapter_execution_consumption_id": consumption.adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": consumption.adapter_execution_consumption_hash,
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
            "consumer_id": consumption.consumer_id,
            "projection": consumption.projection,
            "query_mode": consumption.query_mode,
            "query_text": consumption.query_text,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "invocation_package_type": consumption.invocation_package_type,
            "execution_package_type": consumption.execution_package_type,
            "active_invocation_type": ACTIVE_INVOCATION_TYPE,
            "read_invocation_mode": consumption.read_invocation_mode,
            "read_adapter_contract_id": consumption.read_adapter_contract_id,
            "execution_mode": consumption.execution_mode,
            "active_resolution_strategy": consumption.consumed_resolution_strategy,
            "active_entry_count": consumption.consumed_entry_count,
            "active_response_artifact_entry_ids": tuple(
                consumption.consumed_response_artifact_entry_ids
            ),
            "active_query_response_ids": tuple(
                consumption.consumed_query_response_ids
            ),
            "consumption_type_verified": True,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_invocation_package_verified": True,
            "immutable_execution_package_verified": True,
            "read_adapter_contract_verified": True,
            "bounded_artifact_read_verified": True,
            "single_read_invocation_verified": True,
            "single_use_execution_consumption_verified": True,
            "deterministic_activation_verified": True,
            "adapter_invocation_active": True,
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
            "activation_status": ACTIVATION_STATUS,
        }

        return OracleOperatorQueryResolutionAdapterInvocationActivation(
            **body,
            adapter_invocation_activation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ACTIVATION_SCHEMA_VERSION",
    "ACTIVATION_STATUS",
    "ACTIVE_INVOCATION_TYPE",
    "EXPECTED_CONSUMPTION_STATUS",
    "EXPECTED_EXECUTION_PACKAGE_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionAdapterInvocationActivation",
    "OracleOperatorQueryResolutionAdapterInvocationActivationGate",
    "OracleOperatorQueryResolutionAdapterInvocationActivationInvariantError",
    "stable_hash",
]
