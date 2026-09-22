from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_execution_gate import (
    EXECUTION_STATUS as OOP_034_EXECUTION_STATUS,
    RENDERED_CONSOLE_ARTIFACT_TYPE as OOP_034_RENDERED_CONSOLE_ARTIFACT_TYPE,
    RENDERED_CONSOLE_FORMAT as OOP_034_RENDERED_CONSOLE_FORMAT,
    OracleOperatorConsoleRenderingExecution,
)

SCHEMA_VERSION = "OOP-035"
ENGINE_ID = "OOP-035"
POLICY_ID = "oracle.operator.console-rendering-result-certification-gate.v1"
CERTIFICATION_STATUS = "operator_console_rendering_result_certified"
CERTIFICATION_TYPE = "immutable_rendered_operator_console_result_certification"

EXPECTED_EXECUTION_STATUS = OOP_034_EXECUTION_STATUS
EXPECTED_RENDERED_CONSOLE_ARTIFACT_TYPE = OOP_034_RENDERED_CONSOLE_ARTIFACT_TYPE
EXPECTED_RENDERED_CONSOLE_FORMAT = OOP_034_RENDERED_CONSOLE_FORMAT
EXPECTED_CONSOLE_NAMESPACE = "qseries_v2.oracle_operator.console"


class OracleOperatorConsoleRenderingResultCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
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
class OracleOperatorConsoleRenderingResultCertification:
    operator_console_rendering_result_certification_id: str
    source_operator_console_rendering_execution_id: str
    source_operator_console_rendering_execution_hash: str
    source_operator_console_rendering_consumption_id: str
    source_operator_console_rendering_consumption_hash: str
    source_operator_console_rendering_authorization_id: str
    source_operator_console_rendering_authorization_hash: str
    source_operator_console_result_certification_id: str
    source_operator_console_result_certification_hash: str
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
    operator_console_artifact_type: str
    operator_console_format: str
    rendered_console_artifact_type: str
    rendered_console_format: str
    certification_type: str
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
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
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
    immutable_rendered_console_verified: bool
    read_only_rendered_console_verified: bool
    deterministic_certification_verified: bool
    operator_console_result_certified: bool
    operator_console_rendering_authorized: bool
    operator_console_rendering_authorization_consumed: bool
    operator_console_rendering_allowed: bool
    operator_console_rendering_performed: bool
    operator_console_rendering_result_certified: bool
    operator_presentation_rendering_authorization_ready: bool
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
    certification_status: str
    operator_console_rendering_result_certification_hash: str


class OracleOperatorConsoleRenderingResultCertificationGate:
    @staticmethod
    def _verify(execution: OracleOperatorConsoleRenderingExecution) -> None:
        if not isinstance(execution, OracleOperatorConsoleRenderingExecution):
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "source must be canonical OOP-034 execution"
            )

        body = asdict(execution)
        supplied_hash = body.pop("operator_console_rendering_execution_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "OOP-034 execution hash mismatch"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "OOP-034 execution status mismatch"
            )
        if execution.rendered_console_artifact_type != EXPECTED_RENDERED_CONSOLE_ARTIFACT_TYPE:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console artifact type mismatch"
            )
        if execution.rendered_console_format != EXPECTED_RENDERED_CONSOLE_FORMAT:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console format mismatch"
            )
        if execution.console_namespace != EXPECTED_CONSOLE_NAMESPACE:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "console namespace mismatch"
            )

        if not _valid_sha256(execution.rendered_console_id):
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console id invalid"
            )
        if not _valid_sha256(execution.rendered_console_payload_hash):
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console payload hash invalid"
            )
        if stable_hash(execution.rendered_console_payload) != execution.rendered_console_payload_hash:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console payload hash mismatch"
            )

        rendered = execution.rendered_console_payload
        if rendered.get("rendered_console_id") != execution.rendered_console_id:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console identity mismatch"
            )
        if rendered.get("rendered_console_format") != execution.rendered_console_format:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console format payload mismatch"
            )
        if rendered.get("operator_console_id") != execution.operator_console_id:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "operator console identity mismatch"
            )
        if rendered.get("operator_console_payload_hash") != execution.operator_console_payload_hash:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "operator console payload hash mismatch"
            )
        if rendered.get("operator_session_id") != execution.operator_session_id:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "operator session identity mismatch"
            )
        if rendered.get("research_response_id") != execution.research_response_id:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "research response identity mismatch"
            )
        if rendered.get("research_response_item_count") != execution.research_response_item_count:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "research response item count mismatch"
            )
        if tuple(rendered.get("research_response_items") or ()) != tuple(execution.research_response_items):
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "research response items mismatch"
            )
        sections = tuple(rendered.get("sections") or ())
        if len(sections) != 3:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console sections mismatch"
            )
        expected_section_ids = ("query_context", "research_results", "lineage")
        if tuple(section.get("section_id") for section in sections) != expected_section_ids:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console section order mismatch"
            )
        if rendered.get("read_only") is not True:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console is not read-only"
            )
        if rendered.get("presentation_rendering_disabled") is not True:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "presentation rendering boundary missing"
            )
        if rendered.get("publication_disabled") is not True:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "publication boundary missing"
            )
        if rendered.get("qseries_execution_disabled") is not True:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "Q Series execution boundary missing"
            )

        if stable_hash(execution.operator_console_payload) != execution.operator_console_payload_hash:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "source operator console payload hash mismatch"
            )
        if execution.research_response_item_count < 1:
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "rendered console contains no research response items"
            )
        if execution.research_response_item_count != len(execution.research_response_items):
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "research response cardinality mismatch"
            )

        required = (
            execution.consumption_identity_verified,
            execution.consumption_hash_verified,
            execution.consumption_status_verified,
            execution.render_execution_package_type_verified,
            execution.operator_console_identity_verified,
            execution.operator_console_payload_hash_verified,
            execution.operator_session_identity_verified,
            execution.operator_session_payload_hash_verified,
            execution.research_response_identity_verified,
            execution.research_response_payload_hash_verified,
            execution.research_response_cardinality_verified,
            execution.complete_lineage_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.deterministic_rendering_verified,
            execution.immutable_rendered_console_verified,
            execution.read_only_rendered_console_verified,
            execution.operator_console_result_certified,
            execution.operator_console_rendering_authorization_ready,
            execution.operator_console_rendering_authorized,
            execution.operator_console_rendering_authorization_consumed,
            execution.operator_console_rendering_allowed,
            execution.operator_console_rendering_performed,
            execution.operator_console_rendering_result_certification_ready,
        )
        if not all(required):
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "OOP-034 execution incomplete"
            )

        forbidden = (
            execution.operator_presentation_rendering_allowed,
            execution.operator_presentation_rendering_performed,
            execution.publication_allowed,
            execution.publication_performed,
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
            raise OracleOperatorConsoleRenderingResultCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorConsoleRenderingExecution,
    ) -> OracleOperatorConsoleRenderingResultCertification:
        self._verify(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_id": execution.operator_console_rendering_execution_id,
                "source_execution_hash": execution.operator_console_rendering_execution_hash,
                "rendered_console_id": execution.rendered_console_id,
                "rendered_console_payload_hash": execution.rendered_console_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "operator_console_rendering_result_certification_id": certification_id,
            "source_operator_console_rendering_execution_id": execution.operator_console_rendering_execution_id,
            "source_operator_console_rendering_execution_hash": execution.operator_console_rendering_execution_hash,
            "source_operator_console_rendering_consumption_id": execution.source_operator_console_rendering_consumption_id,
            "source_operator_console_rendering_consumption_hash": execution.source_operator_console_rendering_consumption_hash,
            "source_operator_console_rendering_authorization_id": execution.source_operator_console_rendering_authorization_id,
            "source_operator_console_rendering_authorization_hash": execution.source_operator_console_rendering_authorization_hash,
            "source_operator_console_result_certification_id": execution.source_operator_console_result_certification_id,
            "source_operator_console_result_certification_hash": execution.source_operator_console_result_certification_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "research_response_namespace": execution.research_response_namespace,
            "session_namespace": execution.session_namespace,
            "console_namespace": execution.console_namespace,
            "consumer_id": execution.consumer_id,
            "query_text": execution.query_text,
            "query_mode": execution.query_mode,
            "projection": execution.projection,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "operator_session_artifact_type": execution.operator_session_artifact_type,
            "operator_session_format": execution.operator_session_format,
            "operator_console_artifact_type": execution.operator_console_artifact_type,
            "operator_console_format": execution.operator_console_format,
            "rendered_console_artifact_type": execution.rendered_console_artifact_type,
            "rendered_console_format": execution.rendered_console_format,
            "certification_type": CERTIFICATION_TYPE,
            "research_response_id": execution.research_response_id,
            "research_response_payload_hash": execution.research_response_payload_hash,
            "research_response_item_count": execution.research_response_item_count,
            "research_response_items": tuple(execution.research_response_items),
            "operator_session_id": execution.operator_session_id,
            "operator_session_payload": dict(execution.operator_session_payload),
            "operator_session_payload_hash": execution.operator_session_payload_hash,
            "operator_console_id": execution.operator_console_id,
            "operator_console_payload": dict(execution.operator_console_payload),
            "operator_console_payload_hash": execution.operator_console_payload_hash,
            "rendered_console_id": execution.rendered_console_id,
            "rendered_console_payload": dict(execution.rendered_console_payload),
            "rendered_console_payload_hash": execution.rendered_console_payload_hash,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
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
            "immutable_rendered_console_verified": True,
            "read_only_rendered_console_verified": True,
            "deterministic_certification_verified": True,
            "operator_console_result_certified": True,
            "operator_console_rendering_authorized": True,
            "operator_console_rendering_authorization_consumed": True,
            "operator_console_rendering_allowed": True,
            "operator_console_rendering_performed": True,
            "operator_console_rendering_result_certified": True,
            "operator_presentation_rendering_authorization_ready": True,
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
            "certification_status": CERTIFICATION_STATUS,
        }

        return OracleOperatorConsoleRenderingResultCertification(
            **body,
            operator_console_rendering_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "OracleOperatorConsoleRenderingResultCertification",
    "OracleOperatorConsoleRenderingResultCertificationGate",
    "OracleOperatorConsoleRenderingResultCertificationInvariantError",
    "stable_hash",
]
