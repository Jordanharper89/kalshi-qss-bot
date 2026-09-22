from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_gate import (
    AUTHORIZATION_STATUS as OOP_006_AUTHORIZATION_STATUS,
    OracleOperatorQueryResolutionAuthorization,
)

SCHEMA_VERSION = "OOP-007"
ENGINE_ID = "OOP-007"
POLICY_ID = (
    "oracle.operator.query-resolution-authorization-consumption-gate.v1"
)
CONSUMPTION_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-authorization-consumption.v1"
)
CONSUMPTION_STATUS = (
    "operator_query_resolution_authorization_consumed"
)

EXPECTED_AUTHORIZATION_STATUS = OOP_006_AUTHORIZATION_STATUS
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
READ_INVOCATION_MODE = "authorized_immutable_artifact_read"


class OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
    RuntimeError
):
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
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
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
class OracleOperatorQueryResolutionAuthorizationConsumption:
    resolution_consumption_id: str
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
    read_invocation_mode: str
    consumed_resolution_strategy: str
    consumed_entry_count: int
    consumed_response_artifact_entry_ids: tuple[str, ...]
    consumed_query_response_ids: tuple[str, ...]
    resolution_authorization_type_verified: bool
    resolution_authorization_identity_verified: bool
    resolution_authorization_hash_verified: bool
    resolution_authorization_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    single_bounded_resolution_path_verified: bool
    single_use_consumption_verified: bool
    immutable_read_manifest_verified: bool
    deterministic_consumption_verified: bool
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
    consumption_status: str
    resolution_consumption_hash: str


class OracleOperatorQueryResolutionAuthorizationConsumptionGate:
    @staticmethod
    def _verify_authorization(
        authorization: OracleOperatorQueryResolutionAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            OracleOperatorQueryResolutionAuthorization,
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "source must be the canonical OOP-006 authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop(
            "resolution_authorization_hash",
            None,
        )
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization hash mismatch"
            )

        required_hashes = (
            authorization.resolution_authorization_id,
            authorization.source_resolution_plan_hash,
            authorization.source_query_admission_hash,
            authorization.source_query_request_hash,
            authorization.source_admission_hash,
            authorization.source_dependency_receipt_hash,
            authorization.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 lineage contains invalid hashes"
            )

        if (
            authorization.authorization_status
            != EXPECTED_AUTHORIZATION_STATUS
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization is not active"
            )
        if (
            authorization.operator_namespace
            != EXPECTED_OPERATOR_NAMESPACE
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "operator namespace mismatch"
            )
        if authorization.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "query namespace mismatch"
            )

        if authorization.authorized_entry_count < 1:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "authorization contains no entries"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if authorization.authorized_entry_count != len(
            authorization.authorized_query_response_ids
        ):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "query-response cardinality mismatch"
            )
        if len(
            set(
                authorization.authorized_response_artifact_entry_ids
            )
        ) != authorization.authorized_entry_count:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(
            set(authorization.authorized_query_response_ids)
        ) != authorization.authorized_entry_count:
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            authorization.resolution_plan_type_verified,
            authorization.resolution_plan_identity_verified,
            authorization.resolution_plan_hash_verified,
            authorization.resolution_plan_status_verified,
            authorization.complete_lineage_verified,
            authorization.namespaces_verified,
            authorization.query_parameters_verified,
            authorization.frozen_scope_verified,
            authorization.frozen_scope_preserved,
            authorization.strategy_verified,
            authorization.deterministic_authorization_verified,
            authorization.single_bounded_resolution_path_verified,
            authorization.read_only_resolution_required,
            authorization.query_resolution_allowed,
            authorization.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization is incomplete"
            )

        forbidden_activity = (
            authorization.query_resolution_performed,
            authorization.analytics_artifact_read_performed,
            authorization.analytics_query_execution_allowed,
            authorization.analytics_query_execution_performed,
            authorization.analytics_reexecution_allowed,
            authorization.analytics_reexecution_performed,
            authorization.analytics_database_connection_allowed,
            authorization.analytics_database_connection_performed,
            authorization.analytics_mutation_allowed,
            authorization.analytics_mutation_performed,
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
            raise OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError(
                "OOP-006 authorization contains forbidden activity"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorQueryResolutionAuthorization,
    ) -> OracleOperatorQueryResolutionAuthorizationConsumption:
        self._verify_authorization(authorization)

        resolution_consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_resolution_authorization_id": (
                    authorization.resolution_authorization_id
                ),
                "source_resolution_authorization_hash": (
                    authorization.resolution_authorization_hash
                ),
                "read_invocation_mode": READ_INVOCATION_MODE,
                "consumed_resolution_strategy": (
                    authorization.authorized_resolution_strategy
                ),
                "query_mode": authorization.query_mode,
                "query_text": authorization.query_text,
                "time_scope": authorization.time_scope,
                "sort_order": authorization.sort_order,
                "result_limit": authorization.result_limit,
                "requested_tags": authorization.requested_tags,
                "consumed_response_artifact_entry_ids": (
                    authorization.authorized_response_artifact_entry_ids
                ),
                "consumed_query_response_ids": (
                    authorization.authorized_query_response_ids
                ),
            }
        )

        body = {
            "resolution_consumption_id": resolution_consumption_id,
            "source_resolution_authorization_id": (
                authorization.resolution_authorization_id
            ),
            "source_resolution_authorization_hash": (
                authorization.resolution_authorization_hash
            ),
            "source_resolution_plan_id": (
                authorization.source_resolution_plan_id
            ),
            "source_resolution_plan_hash": (
                authorization.source_resolution_plan_hash
            ),
            "source_query_admission_id": (
                authorization.source_query_admission_id
            ),
            "source_query_admission_hash": (
                authorization.source_query_admission_hash
            ),
            "source_query_request_id": (
                authorization.source_query_request_id
            ),
            "source_query_request_hash": (
                authorization.source_query_request_hash
            ),
            "source_admission_id": authorization.source_admission_id,
            "source_admission_hash": (
                authorization.source_admission_hash
            ),
            "source_dependency_receipt_id": (
                authorization.source_dependency_receipt_id
            ),
            "source_dependency_receipt_hash": (
                authorization.source_dependency_receipt_hash
            ),
            "source_authorization_id": (
                authorization.source_authorization_id
            ),
            "source_authorization_hash": (
                authorization.source_authorization_hash
            ),
            "operator_namespace": authorization.operator_namespace,
            "query_namespace": authorization.query_namespace,
            "consumer_id": authorization.consumer_id,
            "projection": authorization.projection,
            "query_mode": authorization.query_mode,
            "query_text": authorization.query_text,
            "time_scope": authorization.time_scope,
            "sort_order": authorization.sort_order,
            "result_limit": authorization.result_limit,
            "requested_tags": tuple(authorization.requested_tags),
            "read_invocation_mode": READ_INVOCATION_MODE,
            "consumed_resolution_strategy": (
                authorization.authorized_resolution_strategy
            ),
            "consumed_entry_count": (
                authorization.authorized_entry_count
            ),
            "consumed_response_artifact_entry_ids": tuple(
                authorization.authorized_response_artifact_entry_ids
            ),
            "consumed_query_response_ids": tuple(
                authorization.authorized_query_response_ids
            ),
            "resolution_authorization_type_verified": True,
            "resolution_authorization_identity_verified": True,
            "resolution_authorization_hash_verified": True,
            "resolution_authorization_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "single_bounded_resolution_path_verified": True,
            "single_use_consumption_verified": True,
            "immutable_read_manifest_verified": True,
            "deterministic_consumption_verified": True,
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
            "consumption_status": CONSUMPTION_STATUS,
        }

        return OracleOperatorQueryResolutionAuthorizationConsumption(
            **body,
            resolution_consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_SCHEMA_VERSION",
    "CONSUMPTION_STATUS",
    "EXPECTED_AUTHORIZATION_STATUS",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "READ_INVOCATION_MODE",
    "OracleOperatorQueryResolutionAuthorizationConsumption",
    "OracleOperatorQueryResolutionAuthorizationConsumptionGate",
    "OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError",
    "stable_hash",
]
