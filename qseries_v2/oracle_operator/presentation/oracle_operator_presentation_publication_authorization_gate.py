from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_result_certification_gate import (
    CERTIFICATION_STATUS as OOP_039_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_039_CERTIFICATION_TYPE,
    OracleOperatorPresentationRenderingResultCertification,
)

SCHEMA_VERSION = "OOP-040"
ENGINE_ID = "OOP-040"
POLICY_ID = "oracle.operator.presentation-publication-authorization-gate.v1"
AUTHORIZATION_STATUS = "operator_presentation_publication_authorized"
AUTHORIZATION_TYPE = "single_use_immutable_operator_presentation_publication_authorization"
PUBLICATION_INPUT_PACKAGE_TYPE = "certified_rendered_operator_presentation_publication_input_package"
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"

EXPECTED_CERTIFICATION_STATUS = OOP_039_CERTIFICATION_STATUS
EXPECTED_CERTIFICATION_TYPE = OOP_039_CERTIFICATION_TYPE


class OracleOperatorPresentationPublicationAuthorizationInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
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
class OracleOperatorPresentationPublicationAuthorization:
    operator_presentation_publication_authorization_id: str
    source_operator_presentation_rendering_result_certification_id: str
    source_operator_presentation_rendering_result_certification_hash: str
    source_operator_presentation_rendering_execution_id: str
    source_operator_presentation_rendering_execution_hash: str
    source_operator_presentation_rendering_consumption_id: str
    source_operator_presentation_rendering_consumption_hash: str
    source_operator_presentation_rendering_authorization_id: str
    source_operator_presentation_rendering_authorization_hash: str
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
    rendered_presentation_artifact_type: str
    rendered_presentation_format: str
    certification_type: str
    authorization_type: str
    publication_input_package_type: str
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
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    certification_type_verified: bool
    rendered_presentation_identity_verified: bool
    rendered_presentation_payload_hash_verified: bool
    rendered_presentation_artifact_type_verified: bool
    rendered_presentation_format_verified: bool
    rendered_presentation_sections_verified: bool
    rendered_console_identity_verified: bool
    rendered_console_payload_hash_verified: bool
    operator_console_identity_verified: bool
    operator_console_payload_hash_verified: bool
    operator_session_identity_verified: bool
    operator_session_payload_hash_verified: bool
    research_response_identity_verified: bool
    research_response_payload_hash_verified: bool
    research_response_cardinality_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_publication_input_verified: bool
    single_use_authorization_verified: bool
    deterministic_authorization_verified: bool
    read_only_boundary_verified: bool
    operator_presentation_rendering_result_certified: bool
    publication_authorization_ready: bool
    publication_authorized: bool
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
    operator_presentation_publication_authorization_hash: str


class OracleOperatorPresentationPublicationAuthorizationGate:
    @staticmethod
    def _verify(
        certification: OracleOperatorPresentationRenderingResultCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorPresentationRenderingResultCertification,
        ):
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "source must be canonical OOP-039 certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "operator_presentation_rendering_result_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "OOP-039 certification hash mismatch"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "OOP-039 certification status mismatch"
            )
        if certification.certification_type != EXPECTED_CERTIFICATION_TYPE:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "OOP-039 certification type mismatch"
            )
        if certification.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(certification.rendered_presentation_id):
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered presentation id invalid"
            )
        if not _valid_sha256(certification.rendered_presentation_payload_hash):
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered presentation payload hash invalid"
            )
        if stable_hash(certification.rendered_presentation_payload) != certification.rendered_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered presentation payload hash mismatch"
            )

        payload = certification.rendered_presentation_payload
        if payload.get("rendered_presentation_id") != certification.rendered_presentation_id:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered presentation identity mismatch"
            )
        if payload.get("rendered_presentation_format") != certification.rendered_presentation_format:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered presentation format mismatch"
            )
        if payload.get("rendered_console_id") != certification.rendered_console_id:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered console identity mismatch"
            )
        if payload.get("rendered_console_payload_hash") != certification.rendered_console_payload_hash:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered console payload hash mismatch"
            )
        if payload.get("operator_console_id") != certification.operator_console_id:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "operator console identity mismatch"
            )
        if payload.get("operator_session_id") != certification.operator_session_id:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "operator session identity mismatch"
            )
        if payload.get("research_response_id") != certification.research_response_id:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "research response identity mismatch"
            )
        if payload.get("research_response_item_count") != certification.research_response_item_count:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(payload.get("research_response_items") or ()) != tuple(certification.research_response_items):
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "research response items mismatch"
            )

        sections = tuple(payload.get("sections") or ())
        if tuple(section.get("section_id") for section in sections) != (
            "presentation_header",
            "presentation_results",
            "presentation_context",
            "presentation_lineage",
        ):
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered presentation sections mismatch"
            )

        if payload.get("read_only") is not True:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "rendered presentation is not read-only"
            )
        if payload.get("publication_disabled") is not True:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "pre-authorization publication boundary missing"
            )
        if payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "Q Series execution boundary missing"
            )

        required = (
            certification.execution_identity_verified,
            certification.execution_hash_verified,
            certification.execution_status_verified,
            certification.rendered_presentation_identity_verified,
            certification.rendered_presentation_payload_hash_verified,
            certification.rendered_presentation_artifact_type_verified,
            certification.rendered_presentation_format_verified,
            certification.rendered_presentation_sections_verified,
            certification.rendered_console_identity_verified,
            certification.rendered_console_payload_hash_verified,
            certification.operator_console_identity_verified,
            certification.operator_console_payload_hash_verified,
            certification.operator_session_identity_verified,
            certification.operator_session_payload_hash_verified,
            certification.research_response_identity_verified,
            certification.research_response_payload_hash_verified,
            certification.research_response_cardinality_verified,
            certification.complete_lineage_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.immutable_rendered_presentation_verified,
            certification.read_only_rendered_presentation_verified,
            certification.deterministic_certification_verified,
            certification.operator_console_rendering_result_certified,
            certification.operator_presentation_rendering_authorized,
            certification.operator_presentation_rendering_authorization_consumed,
            certification.operator_presentation_rendering_allowed,
            certification.operator_presentation_rendering_performed,
            certification.operator_presentation_rendering_result_certified,
            certification.publication_authorization_ready,
        )
        if not all(required):
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "OOP-039 certification incomplete"
            )

        forbidden = (
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
            raise OracleOperatorPresentationPublicationAuthorizationInvariantError(
                "forbidden downstream activity detected"
            )

    def authorize(
        self,
        *,
        certification: OracleOperatorPresentationRenderingResultCertification,
    ) -> OracleOperatorPresentationPublicationAuthorization:
        self._verify(certification)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_certification_id": certification.operator_presentation_rendering_result_certification_id,
                "source_certification_hash": certification.operator_presentation_rendering_result_certification_hash,
                "rendered_presentation_id": certification.rendered_presentation_id,
                "rendered_presentation_payload_hash": certification.rendered_presentation_payload_hash,
                "authorization_type": AUTHORIZATION_TYPE,
                "publication_input_package_type": PUBLICATION_INPUT_PACKAGE_TYPE,
            }
        )

        body = {
            "operator_presentation_publication_authorization_id": authorization_id,
            "source_operator_presentation_rendering_result_certification_id": certification.operator_presentation_rendering_result_certification_id,
            "source_operator_presentation_rendering_result_certification_hash": certification.operator_presentation_rendering_result_certification_hash,
            "source_operator_presentation_rendering_execution_id": certification.source_operator_presentation_rendering_execution_id,
            "source_operator_presentation_rendering_execution_hash": certification.source_operator_presentation_rendering_execution_hash,
            "source_operator_presentation_rendering_consumption_id": certification.source_operator_presentation_rendering_consumption_id,
            "source_operator_presentation_rendering_consumption_hash": certification.source_operator_presentation_rendering_consumption_hash,
            "source_operator_presentation_rendering_authorization_id": certification.source_operator_presentation_rendering_authorization_id,
            "source_operator_presentation_rendering_authorization_hash": certification.source_operator_presentation_rendering_authorization_hash,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": certification.research_response_namespace,
            "session_namespace": certification.session_namespace,
            "console_namespace": certification.console_namespace,
            "presentation_namespace": certification.presentation_namespace,
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
            "operator_console_artifact_type": certification.operator_console_artifact_type,
            "operator_console_format": certification.operator_console_format,
            "rendered_console_artifact_type": certification.rendered_console_artifact_type,
            "rendered_console_format": certification.rendered_console_format,
            "rendered_presentation_artifact_type": certification.rendered_presentation_artifact_type,
            "rendered_presentation_format": certification.rendered_presentation_format,
            "certification_type": certification.certification_type,
            "authorization_type": AUTHORIZATION_TYPE,
            "publication_input_package_type": PUBLICATION_INPUT_PACKAGE_TYPE,
            "research_response_id": certification.research_response_id,
            "research_response_payload_hash": certification.research_response_payload_hash,
            "research_response_item_count": certification.research_response_item_count,
            "research_response_items": tuple(certification.research_response_items),
            "operator_session_id": certification.operator_session_id,
            "operator_session_payload": dict(certification.operator_session_payload),
            "operator_session_payload_hash": certification.operator_session_payload_hash,
            "operator_console_id": certification.operator_console_id,
            "operator_console_payload": dict(certification.operator_console_payload),
            "operator_console_payload_hash": certification.operator_console_payload_hash,
            "rendered_console_id": certification.rendered_console_id,
            "rendered_console_payload": dict(certification.rendered_console_payload),
            "rendered_console_payload_hash": certification.rendered_console_payload_hash,
            "rendered_presentation_id": certification.rendered_presentation_id,
            "rendered_presentation_payload": dict(certification.rendered_presentation_payload),
            "rendered_presentation_payload_hash": certification.rendered_presentation_payload_hash,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "certification_type_verified": True,
            "rendered_presentation_identity_verified": True,
            "rendered_presentation_payload_hash_verified": True,
            "rendered_presentation_artifact_type_verified": True,
            "rendered_presentation_format_verified": True,
            "rendered_presentation_sections_verified": True,
            "rendered_console_identity_verified": True,
            "rendered_console_payload_hash_verified": True,
            "operator_console_identity_verified": True,
            "operator_console_payload_hash_verified": True,
            "operator_session_identity_verified": True,
            "operator_session_payload_hash_verified": True,
            "research_response_identity_verified": True,
            "research_response_payload_hash_verified": True,
            "research_response_cardinality_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_publication_input_verified": True,
            "single_use_authorization_verified": True,
            "deterministic_authorization_verified": True,
            "read_only_boundary_verified": True,
            "operator_presentation_rendering_result_certified": True,
            "publication_authorization_ready": True,
            "publication_authorized": True,
            "publication_allowed": True,
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

        return OracleOperatorPresentationPublicationAuthorization(
            **body,
            operator_presentation_publication_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_STATUS",
    "AUTHORIZATION_TYPE",
    "PUBLICATION_INPUT_PACKAGE_TYPE",
    "OracleOperatorPresentationPublicationAuthorization",
    "OracleOperatorPresentationPublicationAuthorizationGate",
    "OracleOperatorPresentationPublicationAuthorizationInvariantError",
    "stable_hash",
]
