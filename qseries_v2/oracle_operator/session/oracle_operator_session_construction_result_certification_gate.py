from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.session.oracle_operator_session_construction_execution_gate import (
    EXECUTION_STATUS as OOP_026_EXECUTION_STATUS,
    OPERATOR_SESSION_ARTIFACT_TYPE as OOP_026_OPERATOR_SESSION_ARTIFACT_TYPE,
    OPERATOR_SESSION_FORMAT as OOP_026_OPERATOR_SESSION_FORMAT,
    OracleOperatorSessionConstructionExecution,
)

SCHEMA_VERSION = "OOP-027"
ENGINE_ID = "OOP-027"
POLICY_ID = "oracle.operator.session-construction-result-certification-gate.v1"
CERTIFICATION_STATUS = "operator_session_construction_result_certified"
CERTIFICATION_TYPE = "immutable_operator_session_result_certification"

EXPECTED_EXECUTION_STATUS = OOP_026_EXECUTION_STATUS
EXPECTED_OPERATOR_SESSION_ARTIFACT_TYPE = OOP_026_OPERATOR_SESSION_ARTIFACT_TYPE
EXPECTED_OPERATOR_SESSION_FORMAT = OOP_026_OPERATOR_SESSION_FORMAT


class OracleOperatorSessionConstructionResultCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSessionConstructionResultCertificationInvariantError(
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
class OracleOperatorSessionConstructionResultCertification:
    operator_session_construction_result_certification_id: str
    source_operator_session_construction_execution_id: str
    source_operator_session_construction_execution_hash: str
    source_operator_session_construction_consumption_id: str
    source_operator_session_construction_consumption_hash: str
    source_operator_session_construction_authorization_id: str
    source_operator_session_construction_authorization_hash: str
    source_research_response_result_certification_id: str
    source_research_response_result_certification_hash: str
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
    certification_type: str
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    research_response_items: tuple[Mapping[str, Any], ...]
    operator_session_id: str
    operator_session_payload: Mapping[str, Any]
    operator_session_payload_hash: str
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    execution_package_type_verified: bool
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
    immutable_session_verified: bool
    read_only_session_verified: bool
    deterministic_certification_verified: bool
    operator_session_construction_ready: bool
    operator_session_construction_authorized: bool
    operator_session_construction_authorization_consumed: bool
    operator_session_construction_allowed: bool
    operator_session_construction_performed: bool
    operator_session_result_certified: bool
    operator_console_construction_ready: bool
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
    certification_status: str
    operator_session_construction_result_certification_hash: str


class OracleOperatorSessionConstructionResultCertificationGate:
    @staticmethod
    def _verify(execution: OracleOperatorSessionConstructionExecution) -> None:
        if not isinstance(execution, OracleOperatorSessionConstructionExecution):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "source must be canonical OOP-026 execution"
            )

        body = asdict(execution)
        supplied_hash = body.pop("operator_session_construction_execution_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "OOP-026 execution hash mismatch"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "OOP-026 execution status mismatch"
            )
        if execution.operator_session_artifact_type != EXPECTED_OPERATOR_SESSION_ARTIFACT_TYPE:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session artifact type mismatch"
            )
        if execution.operator_session_format != EXPECTED_OPERATOR_SESSION_FORMAT:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session format mismatch"
            )

        if not _valid_sha256(execution.operator_session_id):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session id invalid"
            )
        if not _valid_sha256(execution.operator_session_payload_hash):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session payload hash invalid"
            )
        if stable_hash(execution.operator_session_payload) != execution.operator_session_payload_hash:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session payload hash mismatch"
            )
        if execution.operator_session_payload.get("operator_session_id") != execution.operator_session_id:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session identity mismatch"
            )
        if execution.operator_session_payload.get("research_response_id") != execution.research_response_id:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response identity mismatch"
            )
        if execution.operator_session_payload.get("research_response_payload_hash") != execution.research_response_payload_hash:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response payload hash mismatch"
            )
        if execution.operator_session_payload.get("research_response_item_count") != execution.research_response_item_count:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response item count mismatch"
            )
        if tuple(execution.operator_session_payload.get("research_response_items") or ()) != tuple(execution.research_response_items):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response items mismatch"
            )
        if execution.operator_session_payload.get("read_only") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session is not read-only"
            )
        if execution.operator_session_payload.get("console_rendering_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "console rendering is not disabled"
            )
        if execution.operator_session_payload.get("presentation_rendering_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "presentation rendering is not disabled"
            )
        if execution.operator_session_payload.get("publication_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "publication is not disabled"
            )
        if execution.operator_session_payload.get("qseries_execution_disabled") is not True:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "Q Series execution is not disabled"
            )

        if execution.research_response_item_count < 1:
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "operator session has no research response items"
            )
        if execution.research_response_item_count != len(execution.research_response_items):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "research response cardinality mismatch"
            )

        required = (
            execution.authorization_consumption_verified,
            execution.authorization_identity_verified,
            execution.authorization_hash_verified,
            execution.authorization_status_verified,
            execution.execution_package_type_verified,
            execution.complete_lineage_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.research_response_identity_verified,
            execution.research_response_payload_hash_verified,
            execution.response_item_cardinality_verified,
            execution.deterministic_session_construction_verified,
            execution.immutable_session_verified,
            execution.read_only_session_verified,
            execution.operator_session_construction_ready,
            execution.operator_session_construction_authorized,
            execution.operator_session_construction_authorization_consumed,
            execution.operator_session_construction_allowed,
            execution.operator_session_construction_performed,
            execution.operator_session_certification_ready,
        )
        if not all(required):
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "OOP-026 execution incomplete"
            )

        forbidden = (
            execution.operator_console_rendering_allowed,
            execution.operator_console_rendering_performed,
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
            raise OracleOperatorSessionConstructionResultCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorSessionConstructionExecution,
    ) -> OracleOperatorSessionConstructionResultCertification:
        self._verify(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_id": execution.operator_session_construction_execution_id,
                "source_execution_hash": execution.operator_session_construction_execution_hash,
                "operator_session_id": execution.operator_session_id,
                "operator_session_payload_hash": execution.operator_session_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "operator_session_construction_result_certification_id": certification_id,
            "source_operator_session_construction_execution_id": execution.operator_session_construction_execution_id,
            "source_operator_session_construction_execution_hash": execution.operator_session_construction_execution_hash,
            "source_operator_session_construction_consumption_id": execution.source_operator_session_construction_consumption_id,
            "source_operator_session_construction_consumption_hash": execution.source_operator_session_construction_consumption_hash,
            "source_operator_session_construction_authorization_id": execution.source_operator_session_construction_authorization_id,
            "source_operator_session_construction_authorization_hash": execution.source_operator_session_construction_authorization_hash,
            "source_research_response_result_certification_id": execution.source_research_response_result_certification_id,
            "source_research_response_result_certification_hash": execution.source_research_response_result_certification_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "research_response_namespace": execution.research_response_namespace,
            "session_namespace": execution.session_namespace,
            "consumer_id": execution.consumer_id,
            "query_text": execution.query_text,
            "query_mode": execution.query_mode,
            "projection": execution.projection,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "execution_package_type": execution.execution_package_type,
            "operator_session_artifact_type": execution.operator_session_artifact_type,
            "operator_session_format": execution.operator_session_format,
            "certification_type": CERTIFICATION_TYPE,
            "research_response_id": execution.research_response_id,
            "research_response_payload_hash": execution.research_response_payload_hash,
            "research_response_item_count": execution.research_response_item_count,
            "research_response_items": tuple(execution.research_response_items),
            "operator_session_id": execution.operator_session_id,
            "operator_session_payload": dict(execution.operator_session_payload),
            "operator_session_payload_hash": execution.operator_session_payload_hash,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "execution_package_type_verified": True,
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
            "immutable_session_verified": True,
            "read_only_session_verified": True,
            "deterministic_certification_verified": True,
            "operator_session_construction_ready": True,
            "operator_session_construction_authorized": True,
            "operator_session_construction_authorization_consumed": True,
            "operator_session_construction_allowed": True,
            "operator_session_construction_performed": True,
            "operator_session_result_certified": True,
            "operator_console_construction_ready": True,
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
            "certification_status": CERTIFICATION_STATUS,
        }

        return OracleOperatorSessionConstructionResultCertification(
            **body,
            operator_session_construction_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "OracleOperatorSessionConstructionResultCertification",
    "OracleOperatorSessionConstructionResultCertificationGate",
    "OracleOperatorSessionConstructionResultCertificationInvariantError",
    "stable_hash",
]
