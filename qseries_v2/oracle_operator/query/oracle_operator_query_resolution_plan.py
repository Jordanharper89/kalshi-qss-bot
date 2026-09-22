from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_request_admission_gate import (
    ADMISSION_STATUS as OOP_004_ADMISSION_STATUS,
    OracleOperatorQueryRequestAdmission,
)

SCHEMA_VERSION = "OOP-005"
ENGINE_ID = "OOP-005"
POLICY_ID = "oracle.operator.query-resolution-plan.v1"
RESOLUTION_PLAN_SCHEMA_VERSION = "oracle.operator.query.resolution-plan.v1"
RESOLUTION_PLAN_STATUS = "operator_query_resolution_planned"

EXPECTED_ADMISSION_STATUS = OOP_004_ADMISSION_STATUS
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"

_ALLOWED_RESOLUTION_STRATEGIES = frozenset(
    {
        "authorized_entry_filter",
        "authorized_response_filter",
        "authorized_entry_and_response_filter",
    }
)


class OracleOperatorQueryResolutionPlanInvariantError(RuntimeError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionPlanInvariantError(
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
class OracleOperatorQueryResolutionPlan:
    resolution_plan_id: str
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
    resolution_strategy: str
    planned_entry_count: int
    planned_response_artifact_entry_ids: tuple[str, ...]
    planned_query_response_ids: tuple[str, ...]
    query_admission_type_verified: bool
    query_admission_identity_verified: bool
    query_admission_hash_verified: bool
    query_admission_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    consumer_identity_verified: bool
    projection_identity_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    resolution_strategy_verified: bool
    deterministic_plan_verified: bool
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
    resolution_plan_status: str
    resolution_plan_hash: str


class OracleOperatorQueryResolutionPlanner:
    @staticmethod
    def _verify_admission(
        admission: OracleOperatorQueryRequestAdmission,
    ) -> None:
        if not isinstance(admission, OracleOperatorQueryRequestAdmission):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "source must be the canonical OOP-004 query admission"
            )

        body = asdict(admission)
        supplied_hash = body.pop("query_admission_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission hash mismatch"
            )

        required_hashes = (
            admission.query_admission_id,
            admission.source_query_request_hash,
            admission.source_admission_hash,
            admission.source_dependency_receipt_hash,
            admission.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 lineage contains invalid hashes"
            )

        if admission.admission_status != EXPECTED_ADMISSION_STATUS:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission is not active"
            )
        if admission.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "operator namespace mismatch"
            )
        if admission.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "query namespace mismatch"
            )

        if admission.admitted_entry_count < 1:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "query admission contains no authorized entries"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if admission.admitted_entry_count != len(
            admission.admitted_query_response_ids
        ):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "query-response cardinality mismatch"
            )

        required_truths = (
            admission.query_request_type_verified,
            admission.query_request_identity_verified,
            admission.query_request_hash_verified,
            admission.query_request_status_verified,
            admission.source_admission_lineage_verified,
            admission.source_dependency_lineage_verified,
            admission.source_authorization_lineage_verified,
            admission.operator_namespace_verified,
            admission.consumer_identity_verified,
            admission.projection_identity_verified,
            admission.query_parameters_verified,
            admission.authorized_scope_verified,
            admission.authorized_scope_frozen,
            admission.deterministic_admission_verified,
            admission.analytics_read_only_dependency_preserved,
            admission.query_resolution_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission is incomplete"
            )

        forbidden_authority = (
            admission.query_resolution_performed,
            admission.analytics_query_execution_allowed,
            admission.analytics_query_execution_performed,
            admission.analytics_reexecution_allowed,
            admission.analytics_reexecution_performed,
            admission.analytics_database_connection_allowed,
            admission.analytics_database_connection_performed,
            admission.analytics_mutation_allowed,
            admission.analytics_mutation_performed,
            admission.operator_session_construction_allowed,
            admission.operator_console_rendering_allowed,
            admission.operator_presentation_rendering_allowed,
            admission.publication_allowed,
            admission.publication_performed,
            admission.qseries_handoff_allowed,
            admission.qseries_execution_allowed,
            admission.qseries_execution_performed,
            admission.order_creation_allowed,
            admission.order_creation_performed,
            admission.funds_movement_allowed,
            admission.funds_movement_performed,
            admission.portfolio_mutation_allowed,
            admission.portfolio_mutation_performed,
        )
        if any(forbidden_authority):
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "OOP-004 query admission contains forbidden activity"
            )

    def plan(
        self,
        *,
        admission: OracleOperatorQueryRequestAdmission,
        resolution_strategy: str = (
            "authorized_entry_and_response_filter"
        ),
    ) -> OracleOperatorQueryResolutionPlan:
        self._verify_admission(admission)

        if resolution_strategy not in _ALLOWED_RESOLUTION_STRATEGIES:
            raise OracleOperatorQueryResolutionPlanInvariantError(
                "unsupported resolution strategy"
            )

        resolution_plan_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_query_admission_id": admission.query_admission_id,
                "source_query_admission_hash": admission.query_admission_hash,
                "resolution_strategy": resolution_strategy,
                "query_mode": admission.query_mode,
                "query_text": admission.query_text,
                "time_scope": admission.time_scope,
                "sort_order": admission.sort_order,
                "result_limit": admission.result_limit,
                "requested_tags": admission.requested_tags,
                "planned_response_artifact_entry_ids": (
                    admission.admitted_response_artifact_entry_ids
                ),
                "planned_query_response_ids": (
                    admission.admitted_query_response_ids
                ),
            }
        )

        body = {
            "resolution_plan_id": resolution_plan_id,
            "source_query_admission_id": admission.query_admission_id,
            "source_query_admission_hash": admission.query_admission_hash,
            "source_query_request_id": admission.source_query_request_id,
            "source_query_request_hash": admission.source_query_request_hash,
            "source_admission_id": admission.source_admission_id,
            "source_admission_hash": admission.source_admission_hash,
            "source_dependency_receipt_id": (
                admission.source_dependency_receipt_id
            ),
            "source_dependency_receipt_hash": (
                admission.source_dependency_receipt_hash
            ),
            "source_authorization_id": admission.source_authorization_id,
            "source_authorization_hash": admission.source_authorization_hash,
            "operator_namespace": admission.operator_namespace,
            "query_namespace": admission.query_namespace,
            "consumer_id": admission.consumer_id,
            "projection": admission.projection,
            "query_mode": admission.query_mode,
            "query_text": admission.query_text,
            "time_scope": admission.time_scope,
            "sort_order": admission.sort_order,
            "result_limit": admission.result_limit,
            "requested_tags": tuple(admission.requested_tags),
            "resolution_strategy": resolution_strategy,
            "planned_entry_count": admission.admitted_entry_count,
            "planned_response_artifact_entry_ids": tuple(
                admission.admitted_response_artifact_entry_ids
            ),
            "planned_query_response_ids": tuple(
                admission.admitted_query_response_ids
            ),
            "query_admission_type_verified": True,
            "query_admission_identity_verified": True,
            "query_admission_hash_verified": True,
            "query_admission_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "consumer_identity_verified": True,
            "projection_identity_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "resolution_strategy_verified": True,
            "deterministic_plan_verified": True,
            "read_only_resolution_required": True,
            "query_resolution_allowed": True,
            "query_resolution_performed": False,
            "analytics_artifact_read_allowed": False,
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
            "resolution_plan_status": RESOLUTION_PLAN_STATUS,
        }

        return OracleOperatorQueryResolutionPlan(
            **body,
            resolution_plan_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "RESOLUTION_PLAN_SCHEMA_VERSION",
    "RESOLUTION_PLAN_STATUS",
    "EXPECTED_ADMISSION_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionPlan",
    "OracleOperatorQueryResolutionPlanner",
    "OracleOperatorQueryResolutionPlanInvariantError",
    "stable_hash",
]
