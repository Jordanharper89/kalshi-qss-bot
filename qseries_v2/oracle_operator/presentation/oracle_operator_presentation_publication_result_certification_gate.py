from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_execution_gate import (
    EXECUTION_STATUS as OOP_042_EXECUTION_STATUS,
    PUBLISHED_PRESENTATION_ARTIFACT_TYPE as OOP_042_PUBLISHED_PRESENTATION_ARTIFACT_TYPE,
    PUBLISHED_PRESENTATION_FORMAT as OOP_042_PUBLISHED_PRESENTATION_FORMAT,
    OracleOperatorPresentationPublicationExecution,
)

SCHEMA_VERSION = "OOP-043"
ENGINE_ID = "OOP-043"
POLICY_ID = "oracle.operator.presentation-publication-result-certification-gate.v1"
CERTIFICATION_STATUS = "operator_presentation_publication_result_certified"
CERTIFICATION_TYPE = "immutable_read_only_operator_presentation_publication_result_certification"

EXPECTED_EXECUTION_STATUS = OOP_042_EXECUTION_STATUS
EXPECTED_PUBLISHED_PRESENTATION_ARTIFACT_TYPE = OOP_042_PUBLISHED_PRESENTATION_ARTIFACT_TYPE
EXPECTED_PUBLISHED_PRESENTATION_FORMAT = OOP_042_PUBLISHED_PRESENTATION_FORMAT
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationPublicationResultCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
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
class OracleOperatorPresentationPublicationResultCertification:
    operator_presentation_publication_result_certification_id: str
    source_operator_presentation_publication_execution_id: str
    source_operator_presentation_publication_execution_hash: str
    source_operator_presentation_publication_consumption_id: str
    source_operator_presentation_publication_consumption_hash: str
    source_operator_presentation_publication_authorization_id: str
    source_operator_presentation_publication_authorization_hash: str
    source_operator_presentation_rendering_result_certification_id: str
    source_operator_presentation_rendering_result_certification_hash: str
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
    published_presentation_artifact_type: str
    published_presentation_format: str
    certification_type: str
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
    rendered_presentation_payload_hash: str
    published_presentation_id: str
    published_presentation_payload: Mapping[str, Any]
    published_presentation_payload_hash: str
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    published_presentation_identity_verified: bool
    published_presentation_payload_hash_verified: bool
    published_presentation_artifact_type_verified: bool
    published_presentation_format_verified: bool
    source_rendered_presentation_identity_verified: bool
    source_rendered_presentation_payload_hash_verified: bool
    research_response_identity_verified: bool
    research_response_cardinality_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_published_presentation_verified: bool
    read_only_publication_verified: bool
    deterministic_certification_verified: bool
    publication_authorization_ready: bool
    publication_authorized: bool
    publication_authorization_consumed: bool
    publication_allowed: bool
    publication_performed: bool
    publication_result_certified: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    certification_status: str
    operator_presentation_publication_result_certification_hash: str


class OracleOperatorPresentationPublicationResultCertificationGate:
    @staticmethod
    def _verify(execution: OracleOperatorPresentationPublicationExecution) -> None:
        if not isinstance(execution, OracleOperatorPresentationPublicationExecution):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "source must be canonical OOP-042 execution"
            )

        body = asdict(execution)
        supplied_hash = body.pop(
            "operator_presentation_publication_execution_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "OOP-042 execution hash mismatch"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "OOP-042 execution status mismatch"
            )
        if execution.published_presentation_artifact_type != EXPECTED_PUBLISHED_PRESENTATION_ARTIFACT_TYPE:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation artifact type mismatch"
            )
        if execution.published_presentation_format != EXPECTED_PUBLISHED_PRESENTATION_FORMAT:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation format mismatch"
            )
        if execution.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(execution.published_presentation_id):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation id invalid"
            )
        if not _valid_sha256(execution.published_presentation_payload_hash):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation payload hash invalid"
            )
        if stable_hash(execution.published_presentation_payload) != execution.published_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation payload hash mismatch"
            )

        payload = execution.published_presentation_payload
        if payload.get("published_presentation_id") != execution.published_presentation_id:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation identity mismatch"
            )
        if payload.get("published_presentation_format") != execution.published_presentation_format:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation format payload mismatch"
            )
        if payload.get("source_rendered_presentation_id") != execution.rendered_presentation_id:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "source rendered presentation identity mismatch"
            )
        if payload.get("source_rendered_presentation_payload_hash") != execution.rendered_presentation_payload_hash:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "source rendered presentation payload hash mismatch"
            )
        if payload.get("research_response_id") != execution.research_response_id:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "research response identity mismatch"
            )
        if payload.get("research_response_item_count") != execution.research_response_item_count:
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "research response cardinality mismatch"
            )
        if tuple(payload.get("research_response_items") or ()) != tuple(execution.research_response_items):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "research response items mismatch"
            )

        boundaries = (
            payload.get("read_only") is True,
            payload.get("publication_completed") is True,
            payload.get("qseries_handoff_disabled") is True,
            payload.get("qseries_execution_disabled") is True,
            payload.get("orders_disabled") is True,
            payload.get("funds_movement_disabled") is True,
            payload.get("portfolio_mutation_disabled") is True,
        )
        if not all(boundaries):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "published presentation safety boundary mismatch"
            )

        required = (
            execution.consumption_identity_verified,
            execution.consumption_hash_verified,
            execution.consumption_status_verified,
            execution.publication_execution_package_type_verified,
            execution.rendered_presentation_identity_verified,
            execution.rendered_presentation_payload_hash_verified,
            execution.rendered_presentation_sections_verified,
            execution.complete_lineage_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.deterministic_publication_verified,
            execution.immutable_published_presentation_verified,
            execution.read_only_publication_verified,
            execution.publication_authorization_ready,
            execution.publication_authorized,
            execution.publication_authorization_consumed,
            execution.publication_allowed,
            execution.publication_performed,
            execution.publication_result_certification_ready,
        )
        if not all(required):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "OOP-042 publication execution incomplete"
            )

        forbidden = (
            execution.qseries_handoff_allowed,
            execution.qseries_execution_allowed,
            execution.qseries_execution_performed,
            execution.order_creation_allowed,
            execution.order_creation_performed,
            execution.funds_movement_allowed,
            execution.funds_movement_performed,
            execution.portfolio_mutation_allowed,
            execution.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorPresentationPublicationResultCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorPresentationPublicationExecution,
    ) -> OracleOperatorPresentationPublicationResultCertification:
        self._verify(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_id": execution.operator_presentation_publication_execution_id,
                "source_execution_hash": execution.operator_presentation_publication_execution_hash,
                "published_presentation_id": execution.published_presentation_id,
                "published_presentation_payload_hash": execution.published_presentation_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "operator_presentation_publication_result_certification_id": certification_id,
            "source_operator_presentation_publication_execution_id": execution.operator_presentation_publication_execution_id,
            "source_operator_presentation_publication_execution_hash": execution.operator_presentation_publication_execution_hash,
            "source_operator_presentation_publication_consumption_id": execution.source_operator_presentation_publication_consumption_id,
            "source_operator_presentation_publication_consumption_hash": execution.source_operator_presentation_publication_consumption_hash,
            "source_operator_presentation_publication_authorization_id": execution.source_operator_presentation_publication_authorization_id,
            "source_operator_presentation_publication_authorization_hash": execution.source_operator_presentation_publication_authorization_hash,
            "source_operator_presentation_rendering_result_certification_id": execution.source_operator_presentation_rendering_result_certification_id,
            "source_operator_presentation_rendering_result_certification_hash": execution.source_operator_presentation_rendering_result_certification_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "research_response_namespace": execution.research_response_namespace,
            "session_namespace": execution.session_namespace,
            "console_namespace": execution.console_namespace,
            "presentation_namespace": execution.presentation_namespace,
            "consumer_id": execution.consumer_id,
            "query_text": execution.query_text,
            "query_mode": execution.query_mode,
            "projection": execution.projection,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "rendered_presentation_artifact_type": execution.rendered_presentation_artifact_type,
            "rendered_presentation_format": execution.rendered_presentation_format,
            "published_presentation_artifact_type": execution.published_presentation_artifact_type,
            "published_presentation_format": execution.published_presentation_format,
            "certification_type": CERTIFICATION_TYPE,
            "research_response_id": execution.research_response_id,
            "research_response_payload_hash": execution.research_response_payload_hash,
            "research_response_item_count": execution.research_response_item_count,
            "research_response_items": tuple(execution.research_response_items),
            "operator_session_id": execution.operator_session_id,
            "operator_session_payload_hash": execution.operator_session_payload_hash,
            "operator_console_id": execution.operator_console_id,
            "operator_console_payload_hash": execution.operator_console_payload_hash,
            "rendered_console_id": execution.rendered_console_id,
            "rendered_console_payload_hash": execution.rendered_console_payload_hash,
            "rendered_presentation_id": execution.rendered_presentation_id,
            "rendered_presentation_payload_hash": execution.rendered_presentation_payload_hash,
            "published_presentation_id": execution.published_presentation_id,
            "published_presentation_payload": dict(execution.published_presentation_payload),
            "published_presentation_payload_hash": execution.published_presentation_payload_hash,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "published_presentation_identity_verified": True,
            "published_presentation_payload_hash_verified": True,
            "published_presentation_artifact_type_verified": True,
            "published_presentation_format_verified": True,
            "source_rendered_presentation_identity_verified": True,
            "source_rendered_presentation_payload_hash_verified": True,
            "research_response_identity_verified": True,
            "research_response_cardinality_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_published_presentation_verified": True,
            "read_only_publication_verified": True,
            "deterministic_certification_verified": True,
            "publication_authorization_ready": True,
            "publication_authorized": True,
            "publication_authorization_consumed": True,
            "publication_allowed": True,
            "publication_performed": True,
            "publication_result_certified": True,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "certification_status": CERTIFICATION_STATUS,
        }

        return OracleOperatorPresentationPublicationResultCertification(
            **body,
            operator_presentation_publication_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "OracleOperatorPresentationPublicationResultCertification",
    "OracleOperatorPresentationPublicationResultCertificationGate",
    "OracleOperatorPresentationPublicationResultCertificationInvariantError",
    "stable_hash",
]
