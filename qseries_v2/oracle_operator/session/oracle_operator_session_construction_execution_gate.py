from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_025_CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE as OOP_025_EXECUTION_PACKAGE_TYPE,
    OracleOperatorSessionConstructionAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-026"
ENGINE_ID = "OOP-026"
POLICY_ID = "oracle.operator.session-construction-execution-gate.v1"
EXECUTION_STATUS = "operator_session_construction_executed"
OPERATOR_SESSION_ARTIFACT_TYPE = "immutable_operator_session_artifact"
OPERATOR_SESSION_FORMAT = "operator_session_v1"

EXPECTED_CONSUMPTION_STATUS = OOP_025_CONSUMPTION_STATUS
EXPECTED_EXECUTION_PACKAGE_TYPE = OOP_025_EXECUTION_PACKAGE_TYPE
EXPECTED_SESSION_NAMESPACE = "qseries_v2.oracle_operator.session"


class OracleOperatorSessionConstructionExecutionInvariantError(RuntimeError):
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
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSessionConstructionExecutionInvariantError(
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
class OracleOperatorSessionConstructionExecution:
    operator_session_construction_execution_id: str
    source_operator_session_construction_consumption_id: str
    source_operator_session_construction_consumption_hash: str
    source_operator_session_construction_authorization_id: str
    source_operator_session_construction_authorization_hash: str
    source_research_response_result_certification_id: str
    source_research_response_result_certification_hash: str
    source_research_response_materialization_execution_id: str
    source_research_response_materialization_execution_hash: str
    operator_namespace: str
    query_namespace: str
    research_response_namespace: str
    session_namespace: str
    consumer_id: str
    query_text: str
    query_mode: str
    projection: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    execution_package_type: str
    operator_session_artifact_type: str
    operator_session_format: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload: Mapping[str, Any]
    operator_session_payload_hash: str
    authorization_consumption_verified: bool
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_status_verified: bool
    execution_package_type_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    response_item_cardinality_verified: bool
    deterministic_session_construction_verified: bool
    immutable_session_verified: bool
    read_only_session_verified: bool
    operator_session_construction_ready: bool
    operator_session_construction_authorized: bool
    operator_session_construction_authorization_consumed: bool
    operator_session_construction_allowed: bool
    operator_session_construction_performed: bool
    operator_session_certification_ready: bool
    operator_console_rendering_allowed: bool
    operator_console_rendering_performed: bool
    operator_presentation_rendering_allowed: bool
    operator_presentation_rendering_performed: bool
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
    execution_status: str
    operator_session_construction_execution_hash: str


class OracleOperatorSessionConstructionExecutionGate:
    @staticmethod
    def _verify(
        consumption: OracleOperatorSessionConstructionAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorSessionConstructionAuthorizationConsumption,
        ):
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "source must be canonical OOP-025 consumption"
            )

        body = asdict(consumption)
        supplied_hash = body.pop("operator_session_construction_consumption_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "OOP-025 consumption hash mismatch"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "OOP-025 consumption status mismatch"
            )
        if consumption.execution_package_type != EXPECTED_EXECUTION_PACKAGE_TYPE:
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "execution package type mismatch"
            )
        if consumption.session_namespace != EXPECTED_SESSION_NAMESPACE:
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "session namespace mismatch"
            )

        if not _valid_sha256(consumption.research_response_id):
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "research response id invalid"
            )
        if not _valid_sha256(consumption.research_response_payload_hash):
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "research response payload hash invalid"
            )
        if stable_hash(consumption.research_response_payload) != consumption.research_response_payload_hash:
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "research response payload hash mismatch"
            )

        count = consumption.research_response_item_count
        if count < 1 or count != len(consumption.research_response_items):
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "research response cardinality mismatch"
            )

        required = (
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_status_verified,
            consumption.authorization_type_verified,
            consumption.session_package_type_verified,
            consumption.research_response_identity_verified,
            consumption.research_response_payload_hash_verified,
            consumption.response_item_cardinality_verified,
            consumption.response_item_identity_verified,
            consumption.source_result_hashes_verified,
            consumption.certified_payload_preservation_verified,
            consumption.complete_lineage_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.immutable_session_input_verified,
            consumption.single_use_consumption_verified,
            consumption.immutable_execution_package_verified,
            consumption.deterministic_consumption_verified,
            consumption.read_only_boundary_verified,
            consumption.research_response_result_certified,
            consumption.operator_session_construction_ready,
            consumption.operator_session_construction_authorized,
            consumption.operator_session_construction_authorization_consumed,
            consumption.operator_session_construction_allowed,
        )
        if not all(required):
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "OOP-025 execution package incomplete"
            )

        forbidden = (
            consumption.operator_session_construction_performed,
            consumption.operator_console_rendering_allowed,
            consumption.operator_console_rendering_performed,
            consumption.operator_presentation_rendering_allowed,
            consumption.operator_presentation_rendering_performed,
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
        if any(forbidden):
            raise OracleOperatorSessionConstructionExecutionInvariantError(
                "forbidden downstream activity detected"
            )

    def execute(
        self,
        *,
        consumption: OracleOperatorSessionConstructionAuthorizationConsumption,
    ) -> OracleOperatorSessionConstructionExecution:
        self._verify(consumption)

        operator_session_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_session_construction_consumption_id,
                "source_consumption_hash": consumption.operator_session_construction_consumption_hash,
                "research_response_id": consumption.research_response_id,
                "research_response_payload_hash": consumption.research_response_payload_hash,
                "operator_session_format": OPERATOR_SESSION_FORMAT,
            }
        )

        session_payload = {
            "operator_session_id": operator_session_id,
            "operator_session_format": OPERATOR_SESSION_FORMAT,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "requested_tags": tuple(consumption.requested_tags),
            "research_response_id": consumption.research_response_id,
            "research_response_payload_hash": consumption.research_response_payload_hash,
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "read_only": True,
            "console_rendering_disabled": True,
            "presentation_rendering_disabled": True,
            "publication_disabled": True,
            "qseries_execution_disabled": True,
        }
        session_payload_hash = stable_hash(session_payload)

        execution_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_session_construction_consumption_id,
                "operator_session_id": operator_session_id,
                "operator_session_payload_hash": session_payload_hash,
            }
        )

        body = {
            "operator_session_construction_execution_id": execution_id,
            "source_operator_session_construction_consumption_id": consumption.operator_session_construction_consumption_id,
            "source_operator_session_construction_consumption_hash": consumption.operator_session_construction_consumption_hash,
            "source_operator_session_construction_authorization_id": consumption.source_operator_session_construction_authorization_id,
            "source_operator_session_construction_authorization_hash": consumption.source_operator_session_construction_authorization_hash,
            "source_research_response_result_certification_id": consumption.source_research_response_result_certification_id,
            "source_research_response_result_certification_hash": consumption.source_research_response_result_certification_hash,
            "source_research_response_materialization_execution_id": consumption.source_research_response_materialization_execution_id,
            "source_research_response_materialization_execution_hash": consumption.source_research_response_materialization_execution_hash,
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "research_response_namespace": consumption.research_response_namespace,
            "session_namespace": consumption.session_namespace,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "execution_package_type": consumption.execution_package_type,
            "operator_session_artifact_type": OPERATOR_SESSION_ARTIFACT_TYPE,
            "operator_session_format": OPERATOR_SESSION_FORMAT,
            "research_response_id": consumption.research_response_id,
            "research_response_payload_hash": consumption.research_response_payload_hash,
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "operator_session_id": operator_session_id,
            "operator_session_payload": session_payload,
            "operator_session_payload_hash": session_payload_hash,
            "authorization_consumption_verified": True,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_status_verified": True,
            "execution_package_type_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "response_item_cardinality_verified": True,
            "deterministic_session_construction_verified": True,
            "immutable_session_verified": True,
            "read_only_session_verified": True,
            "operator_session_construction_ready": True,
            "operator_session_construction_authorized": True,
            "operator_session_construction_authorization_consumed": True,
            "operator_session_construction_allowed": True,
            "operator_session_construction_performed": True,
            "operator_session_certification_ready": True,
            "operator_console_rendering_allowed": False,
            "operator_console_rendering_performed": False,
            "operator_presentation_rendering_allowed": False,
            "operator_presentation_rendering_performed": False,
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
            "execution_status": EXECUTION_STATUS,
        }

        return OracleOperatorSessionConstructionExecution(
            **body,
            operator_session_construction_execution_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "EXECUTION_STATUS",
    "OPERATOR_SESSION_ARTIFACT_TYPE",
    "OPERATOR_SESSION_FORMAT",
    "OracleOperatorSessionConstructionExecution",
    "OracleOperatorSessionConstructionExecutionGate",
    "OracleOperatorSessionConstructionExecutionInvariantError",
    "stable_hash",
]
