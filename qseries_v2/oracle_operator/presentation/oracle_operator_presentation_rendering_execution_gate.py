from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_037_CONSUMPTION_STATUS,
    PRESENTATION_EXECUTION_PACKAGE_TYPE as OOP_037_PRESENTATION_EXECUTION_PACKAGE_TYPE,
    OracleOperatorPresentationRenderingAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-038"
ENGINE_ID = "OOP-038"
POLICY_ID = "oracle.operator.presentation-rendering-execution-gate.v1"
EXECUTION_STATUS = "operator_presentation_rendering_executed"
RENDERED_PRESENTATION_ARTIFACT_TYPE = "immutable_rendered_operator_presentation_artifact"
RENDERED_PRESENTATION_FORMAT = "operator_presentation_rendered_v1"

EXPECTED_CONSUMPTION_STATUS = OOP_037_CONSUMPTION_STATUS
EXPECTED_PRESENTATION_EXECUTION_PACKAGE_TYPE = OOP_037_PRESENTATION_EXECUTION_PACKAGE_TYPE
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationRenderingExecutionInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationRenderingExecutionInvariantError(
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
class OracleOperatorPresentationRenderingExecution:
    operator_presentation_rendering_execution_id: str
    source_operator_presentation_rendering_consumption_id: str
    source_operator_presentation_rendering_consumption_hash: str
    source_operator_presentation_rendering_authorization_id: str
    source_operator_presentation_rendering_authorization_hash: str
    source_operator_console_rendering_result_certification_id: str
    source_operator_console_rendering_result_certification_hash: str
    source_operator_console_rendering_execution_id: str
    source_operator_console_rendering_execution_hash: str
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
    presentation_execution_package_type: str
    rendered_presentation_artifact_type: str
    rendered_presentation_format: str
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
    rendered_presentation_id: str
    rendered_presentation_payload: Mapping[str, Any]
    rendered_presentation_payload_hash: str
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    presentation_execution_package_type_verified: bool
    rendered_console_identity_verified: bool
    rendered_console_payload_hash_verified: bool
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
    deterministic_rendering_verified: bool
    immutable_rendered_presentation_verified: bool
    read_only_rendered_presentation_verified: bool
    operator_console_rendering_result_certified: bool
    operator_presentation_rendering_authorization_ready: bool
    operator_presentation_rendering_authorized: bool
    operator_presentation_rendering_authorization_consumed: bool
    operator_presentation_rendering_allowed: bool
    operator_presentation_rendering_performed: bool
    operator_presentation_rendering_result_certification_ready: bool
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
    execution_status: str
    operator_presentation_rendering_execution_hash: str


class OracleOperatorPresentationRenderingExecutionGate:
    @staticmethod
    def _verify(
        consumption: OracleOperatorPresentationRenderingAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorPresentationRenderingAuthorizationConsumption,
        ):
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "source must be canonical OOP-037 consumption"
            )

        body = asdict(consumption)
        supplied_hash = body.pop(
            "operator_presentation_rendering_consumption_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "OOP-037 consumption hash mismatch"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "OOP-037 consumption status mismatch"
            )
        if consumption.presentation_execution_package_type != EXPECTED_PRESENTATION_EXECUTION_PACKAGE_TYPE:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "presentation execution package type mismatch"
            )
        if consumption.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(consumption.rendered_console_id):
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console id invalid"
            )
        if not _valid_sha256(consumption.rendered_console_payload_hash):
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console payload hash invalid"
            )
        if stable_hash(consumption.rendered_console_payload) != consumption.rendered_console_payload_hash:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console payload hash mismatch"
            )

        rendered = consumption.rendered_console_payload
        if rendered.get("rendered_console_id") != consumption.rendered_console_id:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console identity mismatch"
            )
        if rendered.get("rendered_console_format") != consumption.rendered_console_format:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console format mismatch"
            )
        if rendered.get("operator_console_id") != consumption.operator_console_id:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "operator console identity mismatch"
            )
        if rendered.get("operator_console_payload_hash") != consumption.operator_console_payload_hash:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "operator console payload hash mismatch"
            )
        if rendered.get("operator_session_id") != consumption.operator_session_id:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "operator session identity mismatch"
            )
        if rendered.get("research_response_id") != consumption.research_response_id:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "research response identity mismatch"
            )
        if rendered.get("research_response_item_count") != consumption.research_response_item_count:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(rendered.get("research_response_items") or ()) != tuple(consumption.research_response_items):
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "research response items mismatch"
            )

        sections = tuple(rendered.get("sections") or ())
        if len(sections) != 3:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console sections mismatch"
            )
        if tuple(section.get("section_id") for section in sections) != (
            "query_context",
            "research_results",
            "lineage",
        ):
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console section order mismatch"
            )
        if rendered.get("read_only") is not True:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "rendered console is not read-only"
            )
        if rendered.get("publication_disabled") is not True:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "publication boundary missing"
            )
        if rendered.get("qseries_execution_disabled") is not True:
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "Q Series execution boundary missing"
            )

        required = (
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_status_verified,
            consumption.authorization_type_verified,
            consumption.presentation_input_package_type_verified,
            consumption.rendered_console_identity_verified,
            consumption.rendered_console_payload_hash_verified,
            consumption.rendered_console_artifact_type_verified,
            consumption.rendered_console_format_verified,
            consumption.operator_console_identity_verified,
            consumption.operator_console_payload_hash_verified,
            consumption.operator_session_identity_verified,
            consumption.operator_session_payload_hash_verified,
            consumption.research_response_identity_verified,
            consumption.research_response_payload_hash_verified,
            consumption.research_response_cardinality_verified,
            consumption.rendered_sections_verified,
            consumption.complete_lineage_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.immutable_presentation_input_verified,
            consumption.single_use_consumption_verified,
            consumption.immutable_presentation_execution_package_verified,
            consumption.deterministic_consumption_verified,
            consumption.read_only_boundary_verified,
            consumption.operator_console_rendering_result_certified,
            consumption.operator_presentation_rendering_authorization_ready,
            consumption.operator_presentation_rendering_authorized,
            consumption.operator_presentation_rendering_authorization_consumed,
            consumption.operator_presentation_rendering_allowed,
        )
        if not all(required):
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "OOP-037 execution package incomplete"
            )

        forbidden = (
            consumption.operator_presentation_rendering_performed,
            consumption.publication_authorization_ready,
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
            raise OracleOperatorPresentationRenderingExecutionInvariantError(
                "forbidden downstream activity detected"
            )

    def execute(
        self,
        *,
        consumption: OracleOperatorPresentationRenderingAuthorizationConsumption,
    ) -> OracleOperatorPresentationRenderingExecution:
        self._verify(consumption)

        rendered_presentation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_presentation_rendering_consumption_id,
                "source_consumption_hash": consumption.operator_presentation_rendering_consumption_hash,
                "rendered_console_id": consumption.rendered_console_id,
                "rendered_console_payload_hash": consumption.rendered_console_payload_hash,
                "rendered_presentation_format": RENDERED_PRESENTATION_FORMAT,
            }
        )

        presentation_sections = (
            {
                "section_id": "presentation_header",
                "payload": {
                    "consumer_id": consumption.consumer_id,
                    "query_text": consumption.query_text,
                    "projection": consumption.projection,
                    "time_scope": consumption.time_scope,
                },
            },
            {
                "section_id": "presentation_results",
                "payload": {
                    "research_response_id": consumption.research_response_id,
                    "item_count": consumption.research_response_item_count,
                    "items": tuple(consumption.research_response_items),
                },
            },
            {
                "section_id": "presentation_context",
                "payload": {
                    "query_mode": consumption.query_mode,
                    "sort_order": consumption.sort_order,
                    "result_limit": consumption.result_limit,
                    "requested_tags": tuple(consumption.requested_tags),
                },
            },
            {
                "section_id": "presentation_lineage",
                "payload": {
                    "operator_session_id": consumption.operator_session_id,
                    "operator_console_id": consumption.operator_console_id,
                    "rendered_console_id": consumption.rendered_console_id,
                    "rendered_console_payload_hash": consumption.rendered_console_payload_hash,
                },
            },
        )

        rendered_presentation_payload = {
            "rendered_presentation_id": rendered_presentation_id,
            "rendered_presentation_format": RENDERED_PRESENTATION_FORMAT,
            "rendered_console_id": consumption.rendered_console_id,
            "rendered_console_payload_hash": consumption.rendered_console_payload_hash,
            "operator_console_id": consumption.operator_console_id,
            "operator_session_id": consumption.operator_session_id,
            "research_response_id": consumption.research_response_id,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "sections": presentation_sections,
            "read_only": True,
            "publication_disabled": True,
            "qseries_execution_disabled": True,
        }
        rendered_presentation_payload_hash = stable_hash(
            rendered_presentation_payload
        )

        execution_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_presentation_rendering_consumption_id,
                "rendered_presentation_id": rendered_presentation_id,
                "rendered_presentation_payload_hash": rendered_presentation_payload_hash,
            }
        )

        body = {
            "operator_presentation_rendering_execution_id": execution_id,
            "source_operator_presentation_rendering_consumption_id": consumption.operator_presentation_rendering_consumption_id,
            "source_operator_presentation_rendering_consumption_hash": consumption.operator_presentation_rendering_consumption_hash,
            "source_operator_presentation_rendering_authorization_id": consumption.source_operator_presentation_rendering_authorization_id,
            "source_operator_presentation_rendering_authorization_hash": consumption.source_operator_presentation_rendering_authorization_hash,
            "source_operator_console_rendering_result_certification_id": consumption.source_operator_console_rendering_result_certification_id,
            "source_operator_console_rendering_result_certification_hash": consumption.source_operator_console_rendering_result_certification_hash,
            "source_operator_console_rendering_execution_id": consumption.source_operator_console_rendering_execution_id,
            "source_operator_console_rendering_execution_hash": consumption.source_operator_console_rendering_execution_hash,
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "research_response_namespace": consumption.research_response_namespace,
            "session_namespace": consumption.session_namespace,
            "console_namespace": consumption.console_namespace,
            "presentation_namespace": consumption.presentation_namespace,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "operator_session_artifact_type": consumption.operator_session_artifact_type,
            "operator_session_format": consumption.operator_session_format,
            "operator_console_artifact_type": consumption.operator_console_artifact_type,
            "operator_console_format": consumption.operator_console_format,
            "rendered_console_artifact_type": consumption.rendered_console_artifact_type,
            "rendered_console_format": consumption.rendered_console_format,
            "presentation_execution_package_type": consumption.presentation_execution_package_type,
            "rendered_presentation_artifact_type": RENDERED_PRESENTATION_ARTIFACT_TYPE,
            "rendered_presentation_format": RENDERED_PRESENTATION_FORMAT,
            "research_response_id": consumption.research_response_id,
            "research_response_payload_hash": consumption.research_response_payload_hash,
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "operator_session_id": consumption.operator_session_id,
            "operator_session_payload": dict(consumption.operator_session_payload),
            "operator_session_payload_hash": consumption.operator_session_payload_hash,
            "operator_console_id": consumption.operator_console_id,
            "operator_console_payload": dict(consumption.operator_console_payload),
            "operator_console_payload_hash": consumption.operator_console_payload_hash,
            "rendered_console_id": consumption.rendered_console_id,
            "rendered_console_payload": dict(consumption.rendered_console_payload),
            "rendered_console_payload_hash": consumption.rendered_console_payload_hash,
            "rendered_presentation_id": rendered_presentation_id,
            "rendered_presentation_payload": rendered_presentation_payload,
            "rendered_presentation_payload_hash": rendered_presentation_payload_hash,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "presentation_execution_package_type_verified": True,
            "rendered_console_identity_verified": True,
            "rendered_console_payload_hash_verified": True,
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
            "deterministic_rendering_verified": True,
            "immutable_rendered_presentation_verified": True,
            "read_only_rendered_presentation_verified": True,
            "operator_console_rendering_result_certified": True,
            "operator_presentation_rendering_authorization_ready": True,
            "operator_presentation_rendering_authorized": True,
            "operator_presentation_rendering_authorization_consumed": True,
            "operator_presentation_rendering_allowed": True,
            "operator_presentation_rendering_performed": True,
            "operator_presentation_rendering_result_certification_ready": True,
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
            "execution_status": EXECUTION_STATUS,
        }

        return OracleOperatorPresentationRenderingExecution(
            **body,
            operator_presentation_rendering_execution_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "EXECUTION_STATUS",
    "RENDERED_PRESENTATION_ARTIFACT_TYPE",
    "RENDERED_PRESENTATION_FORMAT",
    "OracleOperatorPresentationRenderingExecution",
    "OracleOperatorPresentationRenderingExecutionGate",
    "OracleOperatorPresentationRenderingExecutionInvariantError",
    "stable_hash",
]
