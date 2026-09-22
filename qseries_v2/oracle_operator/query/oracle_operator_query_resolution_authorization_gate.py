from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_plan import (
    RESOLUTION_PLAN_STATUS as OOP_005_RESOLUTION_PLAN_STATUS,
    OracleOperatorQueryResolutionPlan,
)

SCHEMA_VERSION = "OOP-006"
ENGINE_ID = "OOP-006"
POLICY_ID = "oracle.operator.query-resolution-authorization-gate.v1"
AUTHORIZATION_SCHEMA_VERSION = "oracle.operator.query.resolution-authorization.v1"
AUTHORIZATION_STATUS = "operator_query_resolution_authorized"

EXPECTED_RESOLUTION_PLAN_STATUS = OOP_005_RESOLUTION_PLAN_STATUS
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionAuthorizationInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAuthorizationInvariantError(
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
        and all(c in "0123456789abcdef" for c in value)
    )


@dataclass(frozen=True)
class OracleOperatorQueryResolutionAuthorization:
    resolution_authorization_id: str
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
    authorized_resolution_strategy: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    resolution_plan_type_verified: bool
    resolution_plan_identity_verified: bool
    resolution_plan_hash_verified: bool
    resolution_plan_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    strategy_verified: bool
    deterministic_authorization_verified: bool
    single_bounded_resolution_path_verified: bool
    read_only_resolution_required: bool
    query_resolution_allowed: bool
    query_resolution_performed: bool
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
    resolution_authorization_hash: str


class OracleOperatorQueryResolutionAuthorizationGate:
    @staticmethod
    def _verify_plan(plan: OracleOperatorQueryResolutionPlan) -> None:
        if not isinstance(plan, OracleOperatorQueryResolutionPlan):
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "source must be the canonical OOP-005 resolution plan"
            )
        body = asdict(plan)
        supplied = body.pop("resolution_plan_hash", None)
        if not _valid_sha256(supplied) or stable_hash(body) != supplied:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "OOP-005 resolution plan hash mismatch"
            )
        hashes = (
            plan.resolution_plan_id,
            plan.source_query_admission_hash,
            plan.source_query_request_hash,
            plan.source_admission_hash,
            plan.source_dependency_receipt_hash,
            plan.source_authorization_hash,
        )
        if not all(_valid_sha256(v) for v in hashes):
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "OOP-005 lineage contains invalid hashes"
            )
        if plan.resolution_plan_status != EXPECTED_RESOLUTION_PLAN_STATUS:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "OOP-005 resolution plan is not active"
            )
        if plan.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if plan.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "query namespace mismatch"
            )
        if plan.planned_entry_count < 1:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "resolution plan contains no authorized entries"
            )
        if plan.planned_entry_count != len(plan.planned_response_artifact_entry_ids):
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if plan.planned_entry_count != len(plan.planned_query_response_ids):
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(plan.planned_response_artifact_entry_ids)) != plan.planned_entry_count:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(plan.planned_query_response_ids)) != plan.planned_entry_count:
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "duplicate query-response identities detected"
            )
        required = (
            plan.query_admission_type_verified,
            plan.query_admission_identity_verified,
            plan.query_admission_hash_verified,
            plan.query_admission_status_verified,
            plan.complete_lineage_verified,
            plan.namespaces_verified,
            plan.consumer_identity_verified,
            plan.projection_identity_verified,
            plan.query_parameters_verified,
            plan.frozen_scope_verified,
            plan.frozen_scope_preserved,
            plan.resolution_strategy_verified,
            plan.deterministic_plan_verified,
            plan.read_only_resolution_required,
            plan.query_resolution_allowed,
        )
        if not all(required):
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "OOP-005 resolution plan is incomplete"
            )
        forbidden = (
            plan.query_resolution_performed,
            plan.analytics_artifact_read_allowed,
            plan.analytics_artifact_read_performed,
            plan.analytics_query_execution_allowed,
            plan.analytics_query_execution_performed,
            plan.analytics_reexecution_allowed,
            plan.analytics_reexecution_performed,
            plan.analytics_database_connection_allowed,
            plan.analytics_database_connection_performed,
            plan.analytics_mutation_allowed,
            plan.analytics_mutation_performed,
            plan.operator_session_construction_allowed,
            plan.operator_console_rendering_allowed,
            plan.operator_presentation_rendering_allowed,
            plan.publication_allowed,
            plan.publication_performed,
            plan.qseries_handoff_allowed,
            plan.qseries_execution_allowed,
            plan.qseries_execution_performed,
            plan.order_creation_allowed,
            plan.order_creation_performed,
            plan.funds_movement_allowed,
            plan.funds_movement_performed,
            plan.portfolio_mutation_allowed,
            plan.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorQueryResolutionAuthorizationInvariantError(
                "OOP-005 resolution plan contains forbidden activity"
            )

    def authorize(
        self,
        *,
        plan: OracleOperatorQueryResolutionPlan,
    ) -> OracleOperatorQueryResolutionAuthorization:
        self._verify_plan(plan)
        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_resolution_plan_id": plan.resolution_plan_id,
                "source_resolution_plan_hash": plan.resolution_plan_hash,
                "authorized_resolution_strategy": plan.resolution_strategy,
                "query_mode": plan.query_mode,
                "query_text": plan.query_text,
                "time_scope": plan.time_scope,
                "sort_order": plan.sort_order,
                "result_limit": plan.result_limit,
                "requested_tags": plan.requested_tags,
                "authorized_response_artifact_entry_ids": plan.planned_response_artifact_entry_ids,
                "authorized_query_response_ids": plan.planned_query_response_ids,
            }
        )
        body = {
            "resolution_authorization_id": authorization_id,
            "source_resolution_plan_id": plan.resolution_plan_id,
            "source_resolution_plan_hash": plan.resolution_plan_hash,
            "source_query_admission_id": plan.source_query_admission_id,
            "source_query_admission_hash": plan.source_query_admission_hash,
            "source_query_request_id": plan.source_query_request_id,
            "source_query_request_hash": plan.source_query_request_hash,
            "source_admission_id": plan.source_admission_id,
            "source_admission_hash": plan.source_admission_hash,
            "source_dependency_receipt_id": plan.source_dependency_receipt_id,
            "source_dependency_receipt_hash": plan.source_dependency_receipt_hash,
            "source_authorization_id": plan.source_authorization_id,
            "source_authorization_hash": plan.source_authorization_hash,
            "operator_namespace": plan.operator_namespace,
            "query_namespace": plan.query_namespace,
            "consumer_id": plan.consumer_id,
            "projection": plan.projection,
            "query_mode": plan.query_mode,
            "query_text": plan.query_text,
            "time_scope": plan.time_scope,
            "sort_order": plan.sort_order,
            "result_limit": plan.result_limit,
            "requested_tags": tuple(plan.requested_tags),
            "authorized_resolution_strategy": plan.resolution_strategy,
            "authorized_entry_count": plan.planned_entry_count,
            "authorized_response_artifact_entry_ids": tuple(plan.planned_response_artifact_entry_ids),
            "authorized_query_response_ids": tuple(plan.planned_query_response_ids),
            "resolution_plan_type_verified": True,
            "resolution_plan_identity_verified": True,
            "resolution_plan_hash_verified": True,
            "resolution_plan_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "strategy_verified": True,
            "deterministic_authorization_verified": True,
            "single_bounded_resolution_path_verified": True,
            "read_only_resolution_required": True,
            "query_resolution_allowed": True,
            "query_resolution_performed": False,
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
        return OracleOperatorQueryResolutionAuthorization(
            **body,
            resolution_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "EXPECTED_RESOLUTION_PLAN_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionAuthorization",
    "OracleOperatorQueryResolutionAuthorizationGate",
    "OracleOperatorQueryResolutionAuthorizationInvariantError",
    "stable_hash",
]
