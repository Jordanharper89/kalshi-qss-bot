from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.session.oracle_operator_session_construction_result_certification_gate import (
    CERTIFICATION_STATUS as OOP_027_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_027_CERTIFICATION_TYPE,
    OracleOperatorSessionConstructionResultCertification,
)

SCHEMA_VERSION = "OOP-028"
ENGINE_ID = "OOP-028"
POLICY_ID = "oracle.operator.console-construction-authorization-gate.v1"
AUTHORIZATION_STATUS = "operator_console_construction_authorized"
AUTHORIZATION_TYPE = "single_use_immutable_operator_console_construction_authorization"
CONSOLE_INPUT_PACKAGE_TYPE = "certified_operator_console_construction_input_package"

EXPECTED_CERTIFICATION_STATUS = OOP_027_CERTIFICATION_STATUS
EXPECTED_CERTIFICATION_TYPE = OOP_027_CERTIFICATION_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_SESSION_NAMESPACE = "qseries_v2.oracle_operator.session"
EXPECTED_CONSOLE_NAMESPACE = "qseries_v2.oracle_operator.console"


class OracleOperatorConsoleConstructionAuthorizationInvariantError(RuntimeError):
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
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
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
class OracleOperatorConsoleConstructionAuthorization:
    operator_console_construction_authorization_id: str
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
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload: Mapping[str, Any]
    operator_session_payload_hash: str
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    certification_type_verified: bool
    operator_session_identity_verified: bool
    operator_session_payload_hash_verified: bool
    operator_session_artifact_type_verified: bool
    operator_session_format_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    research_response_cardinality_verified: bool
    session_payload_preservation_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_console_input_verified: bool
    single_use_authorization_verified: bool
    deterministic_authorization_verified: bool
    read_only_boundary_verified: bool
    operator_session_result_certified: bool
    operator_console_construction_ready: bool
    operator_console_construction_authorized: bool
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
    authorization_status: str
    operator_console_construction_authorization_hash: str


class OracleOperatorConsoleConstructionAuthorizationGate:
    @staticmethod
    def _verify(
        certification: OracleOperatorSessionConstructionResultCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorSessionConstructionResultCertification,
        ):
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "source must be canonical OOP-027 certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "operator_session_construction_result_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "OOP-027 certification hash mismatch"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "OOP-027 certification status mismatch"
            )
        if certification.certification_type != EXPECTED_CERTIFICATION_TYPE:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "OOP-027 certification type mismatch"
            )
        if certification.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if certification.session_namespace != EXPECTED_SESSION_NAMESPACE:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "session namespace mismatch"
            )

        if not _valid_sha256(certification.operator_session_id):
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "operator session id invalid"
            )
        if not _valid_sha256(certification.operator_session_payload_hash):
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "operator session payload hash invalid"
            )
        if stable_hash(certification.operator_session_payload) != certification.operator_session_payload_hash:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "operator session payload hash mismatch"
            )

        if certification.operator_session_payload.get("operator_session_id") != certification.operator_session_id:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "operator session identity mismatch"
            )
        if certification.operator_session_payload.get("read_only") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "operator session is not read-only"
            )
        if certification.operator_session_payload.get("console_rendering_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "console rendering boundary not preserved"
            )
        if certification.operator_session_payload.get("presentation_rendering_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "presentation rendering boundary not preserved"
            )
        if certification.operator_session_payload.get("publication_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "publication boundary not preserved"
            )
        if certification.operator_session_payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "Q Series execution boundary not preserved"
            )

        if certification.research_response_item_count < 1:
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "certification contains no response items"
            )
        if certification.research_response_item_count != len(certification.research_response_items):
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "research response cardinality mismatch"
            )

        required = (
            certification.execution_identity_verified,
            certification.execution_hash_verified,
            certification.execution_status_verified,
            certification.execution_package_type_verified,
            certification.operator_session_identity_verified,
            certification.operator_session_payload_hash_verified,
            certification.operator_session_artifact_type_verified,
            certification.operator_session_format_verified,
            certification.research_response_identity_verified,
            certification.research_response_payload_hash_verified,
            certification.research_response_cardinality_verified,
            certification.session_payload_preservation_verified,
            certification.complete_lineage_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.immutable_session_verified,
            certification.read_only_session_verified,
            certification.deterministic_certification_verified,
            certification.operator_session_construction_ready,
            certification.operator_session_construction_authorized,
            certification.operator_session_construction_authorization_consumed,
            certification.operator_session_construction_allowed,
            certification.operator_session_construction_performed,
            certification.operator_session_result_certified,
            certification.operator_console_construction_ready,
        )
        if not all(required):
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "OOP-027 certification incomplete"
            )

        forbidden = (
            certification.operator_console_rendering_allowed,
            certification.operator_console_rendering_performed,
            certification.operator_presentation_rendering_allowed,
            certification.operator_presentation_rendering_performed,
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
        if any(forbidden):
            raise OracleOperatorConsoleConstructionAuthorizationInvariantError(
                "forbidden downstream activity detected"
            )

    def authorize(
        self,
        *,
        certification: OracleOperatorSessionConstructionResultCertification,
    ) -> OracleOperatorConsoleConstructionAuthorization:
        self._verify(certification)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_certification_id": certification.operator_session_construction_result_certification_id,
                "source_certification_hash": certification.operator_session_construction_result_certification_hash,
                "operator_session_id": certification.operator_session_id,
                "operator_session_payload_hash": certification.operator_session_payload_hash,
                "authorization_type": AUTHORIZATION_TYPE,
                "console_input_package_type": CONSOLE_INPUT_PACKAGE_TYPE,
            }
        )

        body = {
            "operator_console_construction_authorization_id": authorization_id,
            "source_operator_session_result_certification_id": certification.operator_session_construction_result_certification_id,
            "source_operator_session_result_certification_hash": certification.operator_session_construction_result_certification_hash,
            "source_operator_session_construction_execution_id": certification.source_operator_session_construction_execution_id,
            "source_operator_session_construction_execution_hash": certification.source_operator_session_construction_execution_hash,
            "source_operator_session_construction_consumption_id": certification.source_operator_session_construction_consumption_id,
            "source_operator_session_construction_consumption_hash": certification.source_operator_session_construction_consumption_hash,
            "source_operator_session_construction_authorization_id": certification.source_operator_session_construction_authorization_id,
            "source_operator_session_construction_authorization_hash": certification.source_operator_session_construction_authorization_hash,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": certification.research_response_namespace,
            "session_namespace": certification.session_namespace,
            "console_namespace": EXPECTED_CONSOLE_NAMESPACE,
            "consumer_id": certification.consumer_id,
            "query_text": certification.query_text,
            "query_mode": certification.query_mode,
            "projection": certification.projection,
            "time_scope": certification.time_scope,
            "sort_order": certification.sort_order,
            "result_limit": certification.result_limit,
            "requested_tags": tuple(certification.requested_tags),
            "operator_session_artifact_type": certification.operator_session_artifact_type,
            "operator_session_format": certification.operator_session_format,
            "certification_type": certification.certification_type,
            "authorization_type": AUTHORIZATION_TYPE,
            "console_input_package_type": CONSOLE_INPUT_PACKAGE_TYPE,
            "research_response_id": certification.research_response_id,
            "research_response_payload_hash": certification.research_response_payload_hash,
            "research_response_item_count": certification.research_response_item_count,
            "research_response_items": tuple(certification.research_response_items),
            "operator_session_id": certification.operator_session_id,
            "operator_session_payload": dict(certification.operator_session_payload),
            "operator_session_payload_hash": certification.operator_session_payload_hash,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "certification_type_verified": True,
            "operator_session_identity_verified": True,
            "operator_session_payload_hash_verified": True,
            "operator_session_artifact_type_verified": True,
            "operator_session_format_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "research_response_cardinality_verified": True,
            "session_payload_preservation_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_console_input_verified": True,
            "single_use_authorization_verified": True,
            "deterministic_authorization_verified": True,
            "read_only_boundary_verified": True,
            "operator_session_result_certified": True,
            "operator_console_construction_ready": True,
            "operator_console_construction_authorized": True,
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
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return OracleOperatorConsoleConstructionAuthorization(
            **body,
            operator_console_construction_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_STATUS",
    "AUTHORIZATION_TYPE",
    "CONSOLE_INPUT_PACKAGE_TYPE",
    "OracleOperatorConsoleConstructionAuthorization",
    "OracleOperatorConsoleConstructionAuthorizationGate",
    "OracleOperatorConsoleConstructionAuthorizationInvariantError",
    "stable_hash",
]
