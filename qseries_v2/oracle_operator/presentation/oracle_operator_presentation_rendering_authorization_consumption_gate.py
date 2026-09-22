from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_authorization_gate import (
    AUTHORIZATION_STATUS as OOP_036_AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE as OOP_036_AUTHORIZATION_TYPE,
    PRESENTATION_INPUT_PACKAGE_TYPE as OOP_036_PRESENTATION_INPUT_PACKAGE_TYPE,
    OracleOperatorPresentationRenderingAuthorization,
)

SCHEMA_VERSION = "OOP-037"
ENGINE_ID = "OOP-037"
POLICY_ID = "oracle.operator.presentation-rendering-authorization-consumption-gate.v1"
CONSUMPTION_STATUS = "operator_presentation_rendering_authorization_consumed"
PRESENTATION_EXECUTION_PACKAGE_TYPE = "single_use_immutable_operator_presentation_rendering_execution_package"

EXPECTED_AUTHORIZATION_STATUS = OOP_036_AUTHORIZATION_STATUS
EXPECTED_AUTHORIZATION_TYPE = OOP_036_AUTHORIZATION_TYPE
EXPECTED_PRESENTATION_INPUT_PACKAGE_TYPE = OOP_036_PRESENTATION_INPUT_PACKAGE_TYPE
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
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
class OracleOperatorPresentationRenderingAuthorizationConsumption:
    operator_presentation_rendering_consumption_id: str
    source_operator_presentation_rendering_authorization_id: str
    source_operator_presentation_rendering_authorization_hash: str
    source_operator_console_rendering_result_certification_id: str
    source_operator_console_rendering_result_certification_hash: str
    source_operator_console_rendering_execution_id: str
    source_operator_console_rendering_execution_hash: str
    source_operator_console_rendering_consumption_id: str
    source_operator_console_rendering_consumption_hash: str
    source_operator_console_rendering_authorization_id: str
    source_operator_console_rendering_authorization_hash: str
    operator_namespace: str
    query_namespace: str
    research_response_namespace: str
    session_namespace: str
    console_namespace: str
    presentation_namespace: str
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
    operator_console_artifact_type: str
    operator_console_format: str
    rendered_console_artifact_type: str
    rendered_console_format: str
    certification_type: str
    authorization_type: str
    presentation_input_package_type: str
    presentation_execution_package_type: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload: Mapping[str, Any]
    operator_session_payload_hash: str
    operator_console_id: str
    operator_console_payload: Mapping[str, Any]
    operator_console_payload_hash: str
    rendered_console_id: str
    rendered_console_payload: Mapping[str, Any]
    rendered_console_payload_hash: str
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_status_verified: bool
    authorization_type_verified: bool
    presentation_input_package_type_verified: bool
    rendered_console_identity_verified: bool
    rendered_console_payload_hash_verified: bool
    rendered_console_artifact_type_verified: bool
    rendered_console_format_verified: bool
    operator_console_identity_verified: bool
    operator_console_payload_hash_verified: bool
    operator_session_identity_verified: bool
    operator_session_payload_hash_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    research_response_cardinality_verified: bool
    rendered_sections_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_presentation_input_verified: bool
    single_use_consumption_verified: bool
    immutable_presentation_execution_package_verified: bool
    deterministic_consumption_verified: bool
    read_only_boundary_verified: bool
    operator_console_rendering_result_certified: bool
    operator_presentation_rendering_authorization_ready: bool
    operator_presentation_rendering_authorized: bool
    operator_presentation_rendering_authorization_consumed: bool
    operator_presentation_rendering_allowed: bool
    operator_presentation_rendering_performed: bool
    publication_authorization_ready: bool
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
    operator_presentation_rendering_consumption_hash: str


class OracleOperatorPresentationRenderingAuthorizationConsumptionGate:
    @staticmethod
    def _verify(
        authorization: OracleOperatorPresentationRenderingAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            OracleOperatorPresentationRenderingAuthorization,
        ):
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "source must be canonical OOP-036 authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop(
            "operator_presentation_rendering_authorization_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "OOP-036 authorization hash mismatch"
            )

        if authorization.authorization_status != EXPECTED_AUTHORIZATION_STATUS:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "OOP-036 authorization status mismatch"
            )
        if authorization.authorization_type != EXPECTED_AUTHORIZATION_TYPE:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "authorization type mismatch"
            )
        if authorization.presentation_input_package_type != EXPECTED_PRESENTATION_INPUT_PACKAGE_TYPE:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "presentation input package type mismatch"
            )
        if authorization.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(authorization.rendered_console_id):
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console id invalid"
            )
        if not _valid_sha256(authorization.rendered_console_payload_hash):
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console payload hash invalid"
            )
        if stable_hash(authorization.rendered_console_payload) != authorization.rendered_console_payload_hash:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console payload hash mismatch"
            )

        rendered = authorization.rendered_console_payload
        if rendered.get("rendered_console_id") != authorization.rendered_console_id:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console identity mismatch"
            )
        if rendered.get("rendered_console_format") != authorization.rendered_console_format:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console format mismatch"
            )
        if rendered.get("operator_console_id") != authorization.operator_console_id:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "operator console identity mismatch"
            )
        if rendered.get("operator_console_payload_hash") != authorization.operator_console_payload_hash:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "operator console payload hash mismatch"
            )
        if rendered.get("operator_session_id") != authorization.operator_session_id:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "operator session identity mismatch"
            )
        if rendered.get("research_response_id") != authorization.research_response_id:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "research response identity mismatch"
            )
        if rendered.get("research_response_item_count") != authorization.research_response_item_count:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(rendered.get("research_response_items") or ()) != tuple(authorization.research_response_items):
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "research response items mismatch"
            )
        sections = tuple(rendered.get("sections") or ())
        if len(sections) != 3:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console sections mismatch"
            )
        if tuple(section.get("section_id") for section in sections) != (
            "query_context",
            "research_results",
            "lineage",
        ):
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console section order mismatch"
            )
        if rendered.get("read_only") is not True:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "rendered console is not read-only"
            )
        if rendered.get("publication_disabled") is not True:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "publication boundary missing"
            )
        if rendered.get("qseries_execution_disabled") is not True:
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "Q Series execution boundary missing"
            )

        required = (
            authorization.certification_identity_verified,
            authorization.certification_hash_verified,
            authorization.certification_status_verified,
            authorization.certification_type_verified,
            authorization.rendered_console_identity_verified,
            authorization.rendered_console_payload_hash_verified,
            authorization.rendered_console_artifact_type_verified,
            authorization.rendered_console_format_verified,
            authorization.operator_console_identity_verified,
            authorization.operator_console_payload_hash_verified,
            authorization.operator_session_identity_verified,
            authorization.operator_session_payload_hash_verified,
            authorization.research_response_identity_verified,
            authorization.research_response_payload_hash_verified,
            authorization.research_response_cardinality_verified,
            authorization.rendered_sections_verified,
            authorization.complete_lineage_verified,
            authorization.frozen_scope_verified,
            authorization.frozen_scope_preserved,
            authorization.immutable_presentation_input_verified,
            authorization.single_use_authorization_verified,
            authorization.deterministic_authorization_verified,
            authorization.read_only_boundary_verified,
            authorization.operator_console_rendering_result_certified,
            authorization.operator_presentation_rendering_authorization_ready,
            authorization.operator_presentation_rendering_authorized,
            authorization.operator_presentation_rendering_allowed,
        )
        if not all(required):
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "OOP-036 authorization incomplete"
            )

        forbidden = (
            authorization.operator_presentation_rendering_performed,
            authorization.publication_authorization_ready,
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
            raise OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError(
                "forbidden downstream activity detected"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorPresentationRenderingAuthorization,
    ) -> OracleOperatorPresentationRenderingAuthorizationConsumption:
        self._verify(authorization)

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_authorization_id": authorization.operator_presentation_rendering_authorization_id,
                "source_authorization_hash": authorization.operator_presentation_rendering_authorization_hash,
                "rendered_console_id": authorization.rendered_console_id,
                "rendered_console_payload_hash": authorization.rendered_console_payload_hash,
                "presentation_execution_package_type": PRESENTATION_EXECUTION_PACKAGE_TYPE,
            }
        )

        body = {
            "operator_presentation_rendering_consumption_id": consumption_id,
            "source_operator_presentation_rendering_authorization_id": authorization.operator_presentation_rendering_authorization_id,
            "source_operator_presentation_rendering_authorization_hash": authorization.operator_presentation_rendering_authorization_hash,
            "source_operator_console_rendering_result_certification_id": authorization.source_operator_console_rendering_result_certification_id,
            "source_operator_console_rendering_result_certification_hash": authorization.source_operator_console_rendering_result_certification_hash,
            "source_operator_console_rendering_execution_id": authorization.source_operator_console_rendering_execution_id,
            "source_operator_console_rendering_execution_hash": authorization.source_operator_console_rendering_execution_hash,
            "source_operator_console_rendering_consumption_id": authorization.source_operator_console_rendering_consumption_id,
            "source_operator_console_rendering_consumption_hash": authorization.source_operator_console_rendering_consumption_hash,
            "source_operator_console_rendering_authorization_id": authorization.source_operator_console_rendering_authorization_id,
            "source_operator_console_rendering_authorization_hash": authorization.source_operator_console_rendering_authorization_hash,
            "operator_namespace": authorization.operator_namespace,
            "query_namespace": authorization.query_namespace,
            "research_response_namespace": authorization.research_response_namespace,
            "session_namespace": authorization.session_namespace,
            "console_namespace": authorization.console_namespace,
            "presentation_namespace": authorization.presentation_namespace,
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
            "operator_console_artifact_type": authorization.operator_console_artifact_type,
            "operator_console_format": authorization.operator_console_format,
            "rendered_console_artifact_type": authorization.rendered_console_artifact_type,
            "rendered_console_format": authorization.rendered_console_format,
            "certification_type": authorization.certification_type,
            "authorization_type": authorization.authorization_type,
            "presentation_input_package_type": authorization.presentation_input_package_type,
            "presentation_execution_package_type": PRESENTATION_EXECUTION_PACKAGE_TYPE,
            "research_response_id": authorization.research_response_id,
            "research_response_payload_hash": authorization.research_response_payload_hash,
            "research_response_item_count": authorization.research_response_item_count,
            "research_response_items": tuple(authorization.research_response_items),
            "operator_session_id": authorization.operator_session_id,
            "operator_session_payload": dict(authorization.operator_session_payload),
            "operator_session_payload_hash": authorization.operator_session_payload_hash,
            "operator_console_id": authorization.operator_console_id,
            "operator_console_payload": dict(authorization.operator_console_payload),
            "operator_console_payload_hash": authorization.operator_console_payload_hash,
            "rendered_console_id": authorization.rendered_console_id,
            "rendered_console_payload": dict(authorization.rendered_console_payload),
            "rendered_console_payload_hash": authorization.rendered_console_payload_hash,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_status_verified": True,
            "authorization_type_verified": True,
            "presentation_input_package_type_verified": True,
            "rendered_console_identity_verified": True,
            "rendered_console_payload_hash_verified": True,
            "rendered_console_artifact_type_verified": True,
            "rendered_console_format_verified": True,
            "operator_console_identity_verified": True,
            "operator_console_payload_hash_verified": True,
            "operator_session_identity_verified": True,
            "operator_session_payload_hash_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "research_response_cardinality_verified": True,
            "rendered_sections_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_presentation_input_verified": True,
            "single_use_consumption_verified": True,
            "immutable_presentation_execution_package_verified": True,
            "deterministic_consumption_verified": True,
            "read_only_boundary_verified": True,
            "operator_console_rendering_result_certified": True,
            "operator_presentation_rendering_authorization_ready": True,
            "operator_presentation_rendering_authorized": True,
            "operator_presentation_rendering_authorization_consumed": True,
            "operator_presentation_rendering_allowed": True,
            "operator_presentation_rendering_performed": False,
            "publication_authorization_ready": False,
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

        return OracleOperatorPresentationRenderingAuthorizationConsumption(
            **body,
            operator_presentation_rendering_consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_STATUS",
    "PRESENTATION_EXECUTION_PACKAGE_TYPE",
    "OracleOperatorPresentationRenderingAuthorizationConsumption",
    "OracleOperatorPresentationRenderingAuthorizationConsumptionGate",
    "OracleOperatorPresentationRenderingAuthorizationConsumptionInvariantError",
    "stable_hash",
]
