from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_041_CONSUMPTION_STATUS,
    PUBLICATION_EXECUTION_PACKAGE_TYPE as OOP_041_PUBLICATION_EXECUTION_PACKAGE_TYPE,
    OracleOperatorPresentationPublicationAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-042"
ENGINE_ID = "OOP-042"
POLICY_ID = "oracle.operator.presentation-publication-execution-gate.v1"
EXECUTION_STATUS = "operator_presentation_publication_executed"
PUBLISHED_PRESENTATION_ARTIFACT_TYPE = "immutable_read_only_published_operator_presentation_artifact"
PUBLISHED_PRESENTATION_FORMAT = "operator_presentation_publication_v1"

EXPECTED_CONSUMPTION_STATUS = OOP_041_CONSUMPTION_STATUS
EXPECTED_PUBLICATION_EXECUTION_PACKAGE_TYPE = OOP_041_PUBLICATION_EXECUTION_PACKAGE_TYPE
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationPublicationExecutionInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationPublicationExecutionInvariantError(
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
class OracleOperatorPresentationPublicationExecution:
    operator_presentation_publication_execution_id: str
    source_operator_presentation_publication_consumption_id: str
    source_operator_presentation_publication_consumption_hash: str
    source_operator_presentation_publication_authorization_id: str
    source_operator_presentation_publication_authorization_hash: str
    source_operator_presentation_rendering_result_certification_id: str
    source_operator_presentation_rendering_result_certification_hash: str
    source_operator_presentation_rendering_execution_id: str
    source_operator_presentation_rendering_execution_hash: str
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
    rendered_presentation_artifact_type: str
    rendered_presentation_format: str
    publication_execution_package_type: str
    published_presentation_artifact_type: str
    published_presentation_format: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload_hash: str
    operator_console_id: str
    operator_console_payload_hash: str
    rendered_console_id: str
    rendered_console_payload_hash: str
    rendered_presentation_id: str
    rendered_presentation_payload: Mapping[str, Any]
    rendered_presentation_payload_hash: str
    published_presentation_id: str
    published_presentation_payload: Mapping[str, Any]
    published_presentation_payload_hash: str
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    publication_execution_package_type_verified: bool
    rendered_presentation_identity_verified: bool
    rendered_presentation_payload_hash_verified: bool
    rendered_presentation_sections_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    deterministic_publication_verified: bool
    immutable_published_presentation_verified: bool
    read_only_publication_verified: bool
    publication_authorization_ready: bool
    publication_authorized: bool
    publication_authorization_consumed: bool
    publication_allowed: bool
    publication_performed: bool
    publication_result_certification_ready: bool
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
    operator_presentation_publication_execution_hash: str


class OracleOperatorPresentationPublicationExecutionGate:
    @staticmethod
    def _verify(
        consumption: OracleOperatorPresentationPublicationAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorPresentationPublicationAuthorizationConsumption,
        ):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "source must be canonical OOP-041 consumption"
            )

        body = asdict(consumption)
        supplied_hash = body.pop(
            "operator_presentation_publication_consumption_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "OOP-041 consumption hash mismatch"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "OOP-041 consumption status mismatch"
            )
        if consumption.publication_execution_package_type != EXPECTED_PUBLICATION_EXECUTION_PACKAGE_TYPE:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "publication execution package type mismatch"
            )
        if consumption.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(consumption.rendered_presentation_id):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation id invalid"
            )
        if not _valid_sha256(consumption.rendered_presentation_payload_hash):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation payload hash invalid"
            )
        if stable_hash(consumption.rendered_presentation_payload) != consumption.rendered_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation payload hash mismatch"
            )

        payload = consumption.rendered_presentation_payload
        if payload.get("rendered_presentation_id") != consumption.rendered_presentation_id:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation identity mismatch"
            )
        if payload.get("rendered_presentation_format") != consumption.rendered_presentation_format:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation format mismatch"
            )
        if payload.get("research_response_id") != consumption.research_response_id:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "research response identity mismatch"
            )
        if payload.get("research_response_item_count") != consumption.research_response_item_count:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(payload.get("research_response_items") or ()) != tuple(consumption.research_response_items):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "research response items mismatch"
            )

        sections = tuple(payload.get("sections") or ())
        if tuple(section.get("section_id") for section in sections) != (
            "presentation_header",
            "presentation_results",
            "presentation_context",
            "presentation_lineage",
        ):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation sections mismatch"
            )
        if payload.get("read_only") is not True:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "rendered presentation is not read-only"
            )
        if payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "Q Series execution boundary missing"
            )

        required = (
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_status_verified,
            consumption.authorization_type_verified,
            consumption.publication_input_package_type_verified,
            consumption.rendered_presentation_identity_verified,
            consumption.rendered_presentation_payload_hash_verified,
            consumption.rendered_presentation_artifact_type_verified,
            consumption.rendered_presentation_format_verified,
            consumption.rendered_presentation_sections_verified,
            consumption.rendered_console_identity_verified,
            consumption.rendered_console_payload_hash_verified,
            consumption.operator_console_identity_verified,
            consumption.operator_console_payload_hash_verified,
            consumption.operator_session_identity_verified,
            consumption.operator_session_payload_hash_verified,
            consumption.research_response_identity_verified,
            consumption.research_response_payload_hash_verified,
            consumption.research_response_cardinality_verified,
            consumption.complete_lineage_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.immutable_publication_input_verified,
            consumption.single_use_consumption_verified,
            consumption.immutable_publication_execution_package_verified,
            consumption.deterministic_consumption_verified,
            consumption.read_only_boundary_verified,
            consumption.operator_presentation_rendering_result_certified,
            consumption.publication_authorization_ready,
            consumption.publication_authorized,
            consumption.publication_authorization_consumed,
            consumption.publication_allowed,
        )
        if not all(required):
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "OOP-041 publication execution package incomplete"
            )

        forbidden = (
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
            raise OracleOperatorPresentationPublicationExecutionInvariantError(
                "forbidden downstream activity detected"
            )

    def execute(
        self,
        *,
        consumption: OracleOperatorPresentationPublicationAuthorizationConsumption,
    ) -> OracleOperatorPresentationPublicationExecution:
        self._verify(consumption)

        published_presentation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_presentation_publication_consumption_id,
                "source_consumption_hash": consumption.operator_presentation_publication_consumption_hash,
                "rendered_presentation_id": consumption.rendered_presentation_id,
                "rendered_presentation_payload_hash": consumption.rendered_presentation_payload_hash,
                "published_presentation_format": PUBLISHED_PRESENTATION_FORMAT,
            }
        )

        published_presentation_payload = {
            "published_presentation_id": published_presentation_id,
            "published_presentation_format": PUBLISHED_PRESENTATION_FORMAT,
            "source_rendered_presentation_id": consumption.rendered_presentation_id,
            "source_rendered_presentation_payload_hash": consumption.rendered_presentation_payload_hash,
            "consumer_id": consumption.consumer_id,
            "query_text": consumption.query_text,
            "query_mode": consumption.query_mode,
            "projection": consumption.projection,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "research_response_id": consumption.research_response_id,
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "operator_session_id": consumption.operator_session_id,
            "operator_console_id": consumption.operator_console_id,
            "rendered_console_id": consumption.rendered_console_id,
            "rendered_presentation_payload": dict(consumption.rendered_presentation_payload),
            "read_only": True,
            "publication_completed": True,
            "qseries_handoff_disabled": True,
            "qseries_execution_disabled": True,
            "orders_disabled": True,
            "funds_movement_disabled": True,
            "portfolio_mutation_disabled": True,
        }
        published_presentation_payload_hash = stable_hash(
            published_presentation_payload
        )

        execution_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_consumption_id": consumption.operator_presentation_publication_consumption_id,
                "published_presentation_id": published_presentation_id,
                "published_presentation_payload_hash": published_presentation_payload_hash,
            }
        )

        body = {
            "operator_presentation_publication_execution_id": execution_id,
            "source_operator_presentation_publication_consumption_id": consumption.operator_presentation_publication_consumption_id,
            "source_operator_presentation_publication_consumption_hash": consumption.operator_presentation_publication_consumption_hash,
            "source_operator_presentation_publication_authorization_id": consumption.source_operator_presentation_publication_authorization_id,
            "source_operator_presentation_publication_authorization_hash": consumption.source_operator_presentation_publication_authorization_hash,
            "source_operator_presentation_rendering_result_certification_id": consumption.source_operator_presentation_rendering_result_certification_id,
            "source_operator_presentation_rendering_result_certification_hash": consumption.source_operator_presentation_rendering_result_certification_hash,
            "source_operator_presentation_rendering_execution_id": consumption.source_operator_presentation_rendering_execution_id,
            "source_operator_presentation_rendering_execution_hash": consumption.source_operator_presentation_rendering_execution_hash,
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
            "rendered_presentation_artifact_type": consumption.rendered_presentation_artifact_type,
            "rendered_presentation_format": consumption.rendered_presentation_format,
            "publication_execution_package_type": consumption.publication_execution_package_type,
            "published_presentation_artifact_type": PUBLISHED_PRESENTATION_ARTIFACT_TYPE,
            "published_presentation_format": PUBLISHED_PRESENTATION_FORMAT,
            "research_response_id": consumption.research_response_id,
            "research_response_payload_hash": consumption.research_response_payload_hash,
            "research_response_item_count": consumption.research_response_item_count,
            "research_response_items": tuple(consumption.research_response_items),
            "operator_session_id": consumption.operator_session_id,
            "operator_session_payload_hash": consumption.operator_session_payload_hash,
            "operator_console_id": consumption.operator_console_id,
            "operator_console_payload_hash": consumption.operator_console_payload_hash,
            "rendered_console_id": consumption.rendered_console_id,
            "rendered_console_payload_hash": consumption.rendered_console_payload_hash,
            "rendered_presentation_id": consumption.rendered_presentation_id,
            "rendered_presentation_payload": dict(consumption.rendered_presentation_payload),
            "rendered_presentation_payload_hash": consumption.rendered_presentation_payload_hash,
            "published_presentation_id": published_presentation_id,
            "published_presentation_payload": published_presentation_payload,
            "published_presentation_payload_hash": published_presentation_payload_hash,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "publication_execution_package_type_verified": True,
            "rendered_presentation_identity_verified": True,
            "rendered_presentation_payload_hash_verified": True,
            "rendered_presentation_sections_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "deterministic_publication_verified": True,
            "immutable_published_presentation_verified": True,
            "read_only_publication_verified": True,
            "publication_authorization_ready": True,
            "publication_authorized": True,
            "publication_authorization_consumed": True,
            "publication_allowed": True,
            "publication_performed": True,
            "publication_result_certification_ready": True,
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

        return OracleOperatorPresentationPublicationExecution(
            **body,
            operator_presentation_publication_execution_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "EXECUTION_STATUS",
    "PUBLISHED_PRESENTATION_ARTIFACT_TYPE",
    "PUBLISHED_PRESENTATION_FORMAT",
    "OracleOperatorPresentationPublicationExecution",
    "OracleOperatorPresentationPublicationExecutionGate",
    "OracleOperatorPresentationPublicationExecutionInvariantError",
    "stable_hash",
]
