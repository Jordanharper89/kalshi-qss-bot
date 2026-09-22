from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.console.oracle_operator_console_construction_authorization_gate import (
    AUTHORIZATION_STATUS as OOP_028_AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE as OOP_028_AUTHORIZATION_TYPE,
    CONSOLE_INPUT_PACKAGE_TYPE as OOP_028_CONSOLE_INPUT_PACKAGE_TYPE,
    OracleOperatorConsoleConstructionAuthorization,
)

SCHEMA_VERSION = "OOP-029"
ENGINE_ID = "OOP-029"
POLICY_ID = "oracle.operator.console-construction-authorization-consumption-gate.v1"
CONSUMPTION_STATUS = "operator_console_construction_authorization_consumed"
EXECUTION_PACKAGE_TYPE = "single_use_immutable_operator_console_construction_execution_package"

EXPECTED_AUTHORIZATION_STATUS = OOP_028_AUTHORIZATION_STATUS
EXPECTED_AUTHORIZATION_TYPE = OOP_028_AUTHORIZATION_TYPE
EXPECTED_CONSOLE_INPUT_PACKAGE_TYPE = OOP_028_CONSOLE_INPUT_PACKAGE_TYPE
EXPECTED_CONSOLE_NAMESPACE = "qseries_v2.oracle_operator.console"


class OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
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
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
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
class OracleOperatorConsoleConstructionAuthorizationConsumption:
    operator_console_construction_consumption_id: str
    source_operator_console_construction_authorization_id: str
    source_operator_console_construction_authorization_hash: str
    source_operator_session_result_certification_id: str
    source_operator_session_result_certification_hash: str
    source_operator_session_construction_execution_id: str
    source_operator_session_construction_execution_hash: str
    source_operator_session_construction_consumption_id: str
    source_operator_session_construction_consumption_hash: str
    source_operator_session_construction_authorization_id: str
    source_operator_session_construction_authorization_hash: str
    operator_namespace: str
    query_namespace: str
    research_response_namespace: str
    session_namespace: str
    console_namespace: str
    consumer_id: str
    query_text: str
    query_mode: str
    projection: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    operator_session_artifact_type: str
    operator_session_format: str
    certification_type: str
    authorization_type: str
    console_input_package_type: str
    execution_package_type: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload: Mapping[str, Any]
    operator_session_payload_hash: str
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_status_verified: bool
    authorization_type_verified: bool
    console_input_package_type_verified: bool
    operator_session_identity_verified: bool
    operator_session_payload_hash_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    research_response_cardinality_verified: bool
    session_payload_preservation_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_console_input_verified: bool
    single_use_consumption_verified: bool
    immutable_execution_package_verified: bool
    deterministic_consumption_verified: bool
    read_only_boundary_verified: bool
    operator_session_result_certified: bool
    operator_console_construction_ready: bool
    operator_console_construction_authorized: bool
    operator_console_construction_authorization_consumed: bool
    operator_console_construction_allowed: bool
    operator_console_construction_performed: bool
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
    consumption_status: str
    operator_console_construction_consumption_hash: str


class OracleOperatorConsoleConstructionAuthorizationConsumptionGate:
    @staticmethod
    def _verify(
        authorization: OracleOperatorConsoleConstructionAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            OracleOperatorConsoleConstructionAuthorization,
        ):
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "source must be canonical OOP-028 authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop(
            "operator_console_construction_authorization_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "OOP-028 authorization hash mismatch"
            )

        if authorization.authorization_status != EXPECTED_AUTHORIZATION_STATUS:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "OOP-028 authorization status mismatch"
            )
        if authorization.authorization_type != EXPECTED_AUTHORIZATION_TYPE:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "authorization type mismatch"
            )
        if authorization.console_input_package_type != EXPECTED_CONSOLE_INPUT_PACKAGE_TYPE:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "console input package type mismatch"
            )
        if authorization.console_namespace != EXPECTED_CONSOLE_NAMESPACE:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "console namespace mismatch"
            )

        if not _valid_sha256(authorization.operator_session_id):
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "operator session id invalid"
            )
        if not _valid_sha256(authorization.operator_session_payload_hash):
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "operator session payload hash invalid"
            )
        if stable_hash(authorization.operator_session_payload) != authorization.operator_session_payload_hash:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "operator session payload hash mismatch"
            )

        if authorization.operator_session_payload.get("operator_session_id") != authorization.operator_session_id:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "operator session identity mismatch"
            )
        if authorization.operator_session_payload.get("read_only") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "operator session is not read-only"
            )
        if authorization.operator_session_payload.get("console_rendering_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "console rendering boundary not preserved"
            )
        if authorization.operator_session_payload.get("presentation_rendering_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "presentation rendering boundary not preserved"
            )
        if authorization.operator_session_payload.get("publication_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "publication boundary not preserved"
            )
        if authorization.operator_session_payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "Q Series execution boundary not preserved"
            )

        if authorization.research_response_item_count < 1:
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "authorization contains no research response items"
            )
        if authorization.research_response_item_count != len(authorization.research_response_items):
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "research response cardinality mismatch"
            )

        required = (
            authorization.certification_identity_verified,
            authorization.certification_hash_verified,
            authorization.certification_status_verified,
            authorization.certification_type_verified,
            authorization.operator_session_identity_verified,
            authorization.operator_session_payload_hash_verified,
            authorization.operator_session_artifact_type_verified,
            authorization.operator_session_format_verified,
            authorization.research_response_identity_verified,
            authorization.research_response_payload_hash_verified,
            authorization.research_response_cardinality_verified,
            authorization.session_payload_preservation_verified,
            authorization.complete_lineage_verified,
            authorization.frozen_scope_verified,
            authorization.frozen_scope_preserved,
            authorization.immutable_console_input_verified,
            authorization.single_use_authorization_verified,
            authorization.deterministic_authorization_verified,
            authorization.read_only_boundary_verified,
            authorization.operator_session_result_certified,
            authorization.operator_console_construction_ready,
            authorization.operator_console_construction_authorized,
            authorization.operator_console_construction_allowed,
        )
        if not all(required):
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "OOP-028 authorization incomplete"
            )

        forbidden = (
            authorization.operator_console_construction_performed,
            authorization.operator_console_rendering_allowed,
            authorization.operator_console_rendering_performed,
            authorization.operator_presentation_rendering_allowed,
            authorization.operator_presentation_rendering_performed,
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
        if any(forbidden):
            raise OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError(
                "forbidden downstream activity detected"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorConsoleConstructionAuthorization,
    ) -> OracleOperatorConsoleConstructionAuthorizationConsumption:
        self._verify(authorization)

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_authorization_id": authorization.operator_console_construction_authorization_id,
                "source_authorization_hash": authorization.operator_console_construction_authorization_hash,
                "operator_session_id": authorization.operator_session_id,
                "operator_session_payload_hash": authorization.operator_session_payload_hash,
                "execution_package_type": EXECUTION_PACKAGE_TYPE,
            }
        )

        body = {
            "operator_console_construction_consumption_id": consumption_id,
            "source_operator_console_construction_authorization_id": authorization.operator_console_construction_authorization_id,
            "source_operator_console_construction_authorization_hash": authorization.operator_console_construction_authorization_hash,
            "source_operator_session_result_certification_id": authorization.source_operator_session_result_certification_id,
            "source_operator_session_result_certification_hash": authorization.source_operator_session_result_certification_hash,
            "source_operator_session_construction_execution_id": authorization.source_operator_session_construction_execution_id,
            "source_operator_session_construction_execution_hash": authorization.source_operator_session_construction_execution_hash,
            "source_operator_session_construction_consumption_id": authorization.source_operator_session_construction_consumption_id,
            "source_operator_session_construction_consumption_hash": authorization.source_operator_session_construction_consumption_hash,
            "source_operator_session_construction_authorization_id": authorization.source_operator_session_construction_authorization_id,
            "source_operator_session_construction_authorization_hash": authorization.source_operator_session_construction_authorization_hash,
            "operator_namespace": authorization.operator_namespace,
            "query_namespace": authorization.query_namespace,
            "research_response_namespace": authorization.research_response_namespace,
            "session_namespace": authorization.session_namespace,
            "console_namespace": authorization.console_namespace,
            "consumer_id": authorization.consumer_id,
            "query_text": authorization.query_text,
            "query_mode": authorization.query_mode,
            "projection": authorization.projection,
            "time_scope": authorization.time_scope,
            "sort_order": authorization.sort_order,
            "result_limit": authorization.result_limit,
            "requested_tags": tuple(authorization.requested_tags),
            "operator_session_artifact_type": authorization.operator_session_artifact_type,
            "operator_session_format": authorization.operator_session_format,
            "certification_type": authorization.certification_type,
            "authorization_type": authorization.authorization_type,
            "console_input_package_type": authorization.console_input_package_type,
            "execution_package_type": EXECUTION_PACKAGE_TYPE,
            "research_response_id": authorization.research_response_id,
            "research_response_payload_hash": authorization.research_response_payload_hash,
            "research_response_item_count": authorization.research_response_item_count,
            "research_response_items": tuple(authorization.research_response_items),
            "operator_session_id": authorization.operator_session_id,
            "operator_session_payload": dict(authorization.operator_session_payload),
            "operator_session_payload_hash": authorization.operator_session_payload_hash,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_status_verified": True,
            "authorization_type_verified": True,
            "console_input_package_type_verified": True,
            "operator_session_identity_verified": True,
            "operator_session_payload_hash_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "research_response_cardinality_verified": True,
            "session_payload_preservation_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_console_input_verified": True,
            "single_use_consumption_verified": True,
            "immutable_execution_package_verified": True,
            "deterministic_consumption_verified": True,
            "read_only_boundary_verified": True,
            "operator_session_result_certified": True,
            "operator_console_construction_ready": True,
            "operator_console_construction_authorized": True,
            "operator_console_construction_authorization_consumed": True,
            "operator_console_construction_allowed": True,
            "operator_console_construction_performed": False,
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
            "consumption_status": CONSUMPTION_STATUS,
        }

        return OracleOperatorConsoleConstructionAuthorizationConsumption(
            **body,
            operator_console_construction_consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_STATUS",
    "EXECUTION_PACKAGE_TYPE",
    "OracleOperatorConsoleConstructionAuthorizationConsumption",
    "OracleOperatorConsoleConstructionAuthorizationConsumptionGate",
    "OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError",
    "stable_hash",
]
