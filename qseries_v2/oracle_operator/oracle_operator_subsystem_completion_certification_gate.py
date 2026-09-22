from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_readiness_gate import (
    READINESS_RECORD_TYPE as OOP_046_READINESS_RECORD_TYPE,
    READINESS_STATUS as OOP_046_READINESS_STATUS,
    READINESS_TYPE as OOP_046_READINESS_TYPE,
    OracleOperatorSubsystemCompletionReadiness,
)

SCHEMA_VERSION = "OOP-047"
ENGINE_ID = "OOP-047"
POLICY_ID = "oracle.operator-subsystem-completion-certification-gate.v1"
CERTIFICATION_STATUS = "oracle_operator_subsystem_completion_certified"
CERTIFICATION_TYPE = "terminal_read_only_oracle_operator_subsystem_completion_certification"
FREEZE_RECORD_TYPE = "immutable_oracle_operator_subsystem_completion_freeze_record"

EXPECTED_READINESS_STATUS = OOP_046_READINESS_STATUS
EXPECTED_READINESS_TYPE = OOP_046_READINESS_TYPE
EXPECTED_READINESS_RECORD_TYPE = OOP_046_READINESS_RECORD_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"


class OracleOperatorSubsystemCompletionCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSubsystemCompletionCertificationInvariantError(
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
class OracleOperatorSubsystemCompletionCertification:
    oracle_operator_subsystem_completion_certification_id: str
    source_completion_readiness_id: str
    source_completion_readiness_hash: str
    source_readiness_record_id: str
    source_readiness_record_payload_hash: str
    source_presentation_subsystem_completion_certification_id: str
    source_presentation_subsystem_completion_certification_hash: str
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
    research_response_id: str
    research_response_payload_hash: str
    research_response_item_count: int
    operator_session_id: str
    operator_session_payload_hash: str
    operator_console_id: str
    operator_console_payload_hash: str
    rendered_console_id: str
    rendered_console_payload_hash: str
    rendered_presentation_id: str
    rendered_presentation_payload_hash: str
    published_presentation_id: str
    published_presentation_payload_hash: str
    presentation_freeze_record_id: str
    presentation_freeze_record_payload_hash: str
    readiness_type: str
    readiness_record_type: str
    certification_type: str
    freeze_record_type: str
    freeze_record_id: str
    freeze_record_payload: Mapping[str, Any]
    freeze_record_payload_hash: str
    readiness_identity_verified: bool
    readiness_hash_verified: bool
    readiness_status_verified: bool
    readiness_type_verified: bool
    readiness_record_type_verified: bool
    readiness_record_identity_verified: bool
    readiness_record_payload_hash_verified: bool
    operator_namespace_verified: bool
    query_boundary_verified: bool
    research_response_boundary_verified: bool
    session_boundary_verified: bool
    console_boundary_verified: bool
    presentation_boundary_verified: bool
    publication_chain_completion_verified: bool
    presentation_subsystem_completion_verified: bool
    complete_lineage_verified: bool
    deterministic_certification_verified: bool
    immutable_freeze_record_verified: bool
    read_only_operator_subsystem_verified: bool
    operator_query_boundary_complete: bool
    operator_research_response_boundary_complete: bool
    operator_session_boundary_complete: bool
    operator_console_boundary_complete: bool
    operator_presentation_boundary_complete: bool
    operator_presentation_subsystem_completion_certified: bool
    operator_presentation_subsystem_frozen: bool
    oracle_operator_subsystem_completion_ready: bool
    oracle_operator_subsystem_completion_certified: bool
    oracle_operator_subsystem_frozen: bool
    further_operator_builds_required: bool
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
    oracle_operator_subsystem_completion_certification_hash: str


class OracleOperatorSubsystemCompletionCertificationGate:
    @staticmethod
    def _verify(readiness: OracleOperatorSubsystemCompletionReadiness) -> None:
        if not isinstance(readiness, OracleOperatorSubsystemCompletionReadiness):
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "source must be canonical OOP-046 completion readiness"
            )

        body = asdict(readiness)
        supplied_hash = body.pop(
            "oracle_operator_subsystem_completion_readiness_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "OOP-046 readiness hash mismatch"
            )

        if readiness.readiness_status != EXPECTED_READINESS_STATUS:
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "OOP-046 readiness status mismatch"
            )
        if readiness.readiness_type != EXPECTED_READINESS_TYPE:
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "OOP-046 readiness type mismatch"
            )
        if readiness.readiness_record_type != EXPECTED_READINESS_RECORD_TYPE:
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "OOP-046 readiness record type mismatch"
            )
        if readiness.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "operator namespace mismatch"
            )

        if not _valid_sha256(readiness.readiness_record_id):
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "readiness record id invalid"
            )
        if not _valid_sha256(readiness.readiness_record_payload_hash):
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "readiness record payload hash invalid"
            )
        if stable_hash(readiness.readiness_record_payload) != readiness.readiness_record_payload_hash:
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "readiness record payload hash mismatch"
            )

        payload = readiness.readiness_record_payload
        required_payload_state = (
            payload.get("readiness_record_id") == readiness.readiness_record_id,
            payload.get("operator_namespace") == readiness.operator_namespace,
            payload.get("query_boundary_complete") is True,
            payload.get("research_response_boundary_complete") is True,
            payload.get("session_boundary_complete") is True,
            payload.get("console_boundary_complete") is True,
            payload.get("presentation_boundary_complete") is True,
            payload.get("operator_subsystem_completion_ready") is True,
            payload.get("operator_subsystem_completion_certified") is False,
            payload.get("further_operator_builds_required") is True,
            payload.get("read_only") is True,
            payload.get("qseries_handoff_disabled") is True,
            payload.get("qseries_execution_disabled") is True,
            payload.get("orders_disabled") is True,
            payload.get("funds_movement_disabled") is True,
            payload.get("portfolio_mutation_disabled") is True,
        )
        if not all(required_payload_state):
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "OOP-046 readiness record state mismatch"
            )

        required = (
            readiness.presentation_certification_identity_verified,
            readiness.presentation_certification_hash_verified,
            readiness.presentation_certification_status_verified,
            readiness.presentation_certification_type_verified,
            readiness.presentation_freeze_record_type_verified,
            readiness.presentation_freeze_record_identity_verified,
            readiness.presentation_freeze_record_payload_hash_verified,
            readiness.operator_namespace_verified,
            readiness.presentation_namespace_verified,
            readiness.query_boundary_verified,
            readiness.research_response_boundary_verified,
            readiness.session_boundary_verified,
            readiness.console_boundary_verified,
            readiness.presentation_boundary_verified,
            readiness.publication_chain_completion_verified,
            readiness.complete_lineage_verified,
            readiness.frozen_scope_verified,
            readiness.frozen_scope_preserved,
            readiness.deterministic_readiness_verified,
            readiness.immutable_readiness_record_verified,
            readiness.read_only_operator_subsystem_verified,
            readiness.operator_presentation_subsystem_completion_certified,
            readiness.operator_presentation_subsystem_frozen,
            readiness.operator_query_boundary_complete,
            readiness.operator_research_response_boundary_complete,
            readiness.operator_session_boundary_complete,
            readiness.operator_console_boundary_complete,
            readiness.operator_presentation_boundary_complete,
            readiness.oracle_operator_subsystem_completion_ready,
            readiness.further_operator_builds_required,
        )
        if not all(required):
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "OOP-046 completion readiness is incomplete"
            )
        if readiness.oracle_operator_subsystem_completion_certified:
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "source readiness is already certified"
            )

        forbidden = (
            readiness.qseries_handoff_allowed,
            readiness.qseries_execution_allowed,
            readiness.qseries_execution_performed,
            readiness.order_creation_allowed,
            readiness.order_creation_performed,
            readiness.funds_movement_allowed,
            readiness.funds_movement_performed,
            readiness.portfolio_mutation_allowed,
            readiness.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorSubsystemCompletionCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        readiness: OracleOperatorSubsystemCompletionReadiness,
    ) -> OracleOperatorSubsystemCompletionCertification:
        self._verify(readiness)

        freeze_record_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_completion_readiness_id": readiness.oracle_operator_subsystem_completion_readiness_id,
                "source_completion_readiness_hash": readiness.oracle_operator_subsystem_completion_readiness_hash,
                "source_readiness_record_id": readiness.readiness_record_id,
                "source_readiness_record_payload_hash": readiness.readiness_record_payload_hash,
                "freeze_record_type": FREEZE_RECORD_TYPE,
            }
        )

        freeze_record_payload = {
            "freeze_record_id": freeze_record_id,
            "freeze_record_type": FREEZE_RECORD_TYPE,
            "operator_namespace": readiness.operator_namespace,
            "source_completion_readiness_id": readiness.oracle_operator_subsystem_completion_readiness_id,
            "source_completion_readiness_hash": readiness.oracle_operator_subsystem_completion_readiness_hash,
            "source_readiness_record_id": readiness.readiness_record_id,
            "source_readiness_record_payload_hash": readiness.readiness_record_payload_hash,
            "source_presentation_subsystem_completion_certification_id": readiness.source_presentation_subsystem_completion_certification_id,
            "source_presentation_subsystem_completion_certification_hash": readiness.source_presentation_subsystem_completion_certification_hash,
            "query_boundary_complete": True,
            "research_response_boundary_complete": True,
            "session_boundary_complete": True,
            "console_boundary_complete": True,
            "presentation_boundary_complete": True,
            "operator_subsystem_complete": True,
            "operator_subsystem_completion_certified": True,
            "operator_subsystem_frozen": True,
            "further_operator_builds_required": False,
            "read_only": True,
            "qseries_handoff_disabled": True,
            "qseries_execution_disabled": True,
            "orders_disabled": True,
            "funds_movement_disabled": True,
            "portfolio_mutation_disabled": True,
        }
        freeze_record_payload_hash = stable_hash(freeze_record_payload)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "freeze_record_id": freeze_record_id,
                "freeze_record_payload_hash": freeze_record_payload_hash,
                "certification_type": CERTIFICATION_TYPE,
            }
        )

        body = {
            "oracle_operator_subsystem_completion_certification_id": certification_id,
            "source_completion_readiness_id": readiness.oracle_operator_subsystem_completion_readiness_id,
            "source_completion_readiness_hash": readiness.oracle_operator_subsystem_completion_readiness_hash,
            "source_readiness_record_id": readiness.readiness_record_id,
            "source_readiness_record_payload_hash": readiness.readiness_record_payload_hash,
            "source_presentation_subsystem_completion_certification_id": readiness.source_presentation_subsystem_completion_certification_id,
            "source_presentation_subsystem_completion_certification_hash": readiness.source_presentation_subsystem_completion_certification_hash,
            "operator_namespace": readiness.operator_namespace,
            "query_namespace": readiness.query_namespace,
            "research_response_namespace": readiness.research_response_namespace,
            "session_namespace": readiness.session_namespace,
            "console_namespace": readiness.console_namespace,
            "presentation_namespace": readiness.presentation_namespace,
            "consumer_id": readiness.consumer_id,
            "query_text": readiness.query_text,
            "query_mode": readiness.query_mode,
            "projection": readiness.projection,
            "time_scope": readiness.time_scope,
            "sort_order": readiness.sort_order,
            "result_limit": readiness.result_limit,
            "requested_tags": tuple(readiness.requested_tags),
            "research_response_id": readiness.research_response_id,
            "research_response_payload_hash": readiness.research_response_payload_hash,
            "research_response_item_count": readiness.research_response_item_count,
            "operator_session_id": readiness.operator_session_id,
            "operator_session_payload_hash": readiness.operator_session_payload_hash,
            "operator_console_id": readiness.operator_console_id,
            "operator_console_payload_hash": readiness.operator_console_payload_hash,
            "rendered_console_id": readiness.rendered_console_id,
            "rendered_console_payload_hash": readiness.rendered_console_payload_hash,
            "rendered_presentation_id": readiness.rendered_presentation_id,
            "rendered_presentation_payload_hash": readiness.rendered_presentation_payload_hash,
            "published_presentation_id": readiness.published_presentation_id,
            "published_presentation_payload_hash": readiness.published_presentation_payload_hash,
            "presentation_freeze_record_id": readiness.presentation_freeze_record_id,
            "presentation_freeze_record_payload_hash": readiness.presentation_freeze_record_payload_hash,
            "readiness_type": readiness.readiness_type,
            "readiness_record_type": readiness.readiness_record_type,
            "certification_type": CERTIFICATION_TYPE,
            "freeze_record_type": FREEZE_RECORD_TYPE,
            "freeze_record_id": freeze_record_id,
            "freeze_record_payload": freeze_record_payload,
            "freeze_record_payload_hash": freeze_record_payload_hash,
            "readiness_identity_verified": True,
            "readiness_hash_verified": True,
            "readiness_status_verified": True,
            "readiness_type_verified": True,
            "readiness_record_type_verified": True,
            "readiness_record_identity_verified": True,
            "readiness_record_payload_hash_verified": True,
            "operator_namespace_verified": True,
            "query_boundary_verified": True,
            "research_response_boundary_verified": True,
            "session_boundary_verified": True,
            "console_boundary_verified": True,
            "presentation_boundary_verified": True,
            "publication_chain_completion_verified": True,
            "presentation_subsystem_completion_verified": True,
            "complete_lineage_verified": True,
            "deterministic_certification_verified": True,
            "immutable_freeze_record_verified": True,
            "read_only_operator_subsystem_verified": True,
            "operator_query_boundary_complete": True,
            "operator_research_response_boundary_complete": True,
            "operator_session_boundary_complete": True,
            "operator_console_boundary_complete": True,
            "operator_presentation_boundary_complete": True,
            "operator_presentation_subsystem_completion_certified": True,
            "operator_presentation_subsystem_frozen": True,
            "oracle_operator_subsystem_completion_ready": True,
            "oracle_operator_subsystem_completion_certified": True,
            "oracle_operator_subsystem_frozen": True,
            "further_operator_builds_required": False,
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

        return OracleOperatorSubsystemCompletionCertification(
            **body,
            oracle_operator_subsystem_completion_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "FREEZE_RECORD_TYPE",
    "OracleOperatorSubsystemCompletionCertification",
    "OracleOperatorSubsystemCompletionCertificationGate",
    "OracleOperatorSubsystemCompletionCertificationInvariantError",
    "stable_hash",
]
