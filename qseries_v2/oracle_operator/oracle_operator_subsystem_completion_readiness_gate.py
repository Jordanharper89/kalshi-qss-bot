from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_subsystem_completion_certification_gate import (
    CERTIFICATION_STATUS as OOP_045_CERTIFICATION_STATUS,
    CERTIFICATION_TYPE as OOP_045_CERTIFICATION_TYPE,
    FREEZE_RECORD_TYPE as OOP_045_FREEZE_RECORD_TYPE,
    OracleOperatorPresentationSubsystemCompletionCertification,
)

SCHEMA_VERSION = "OOP-046"
ENGINE_ID = "OOP-046"
POLICY_ID = "oracle.operator-subsystem-completion-readiness-gate.v1"
READINESS_STATUS = "oracle_operator_subsystem_completion_ready"
READINESS_TYPE = "terminal_read_only_oracle_operator_subsystem_completion_readiness"
READINESS_RECORD_TYPE = "immutable_oracle_operator_subsystem_completion_readiness_record"

EXPECTED_CERTIFICATION_STATUS = OOP_045_CERTIFICATION_STATUS
EXPECTED_CERTIFICATION_TYPE = OOP_045_CERTIFICATION_TYPE
EXPECTED_FREEZE_RECORD_TYPE = OOP_045_FREEZE_RECORD_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorSubsystemCompletionReadinessInvariantError(RuntimeError):
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
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorSubsystemCompletionReadinessInvariantError(
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
class OracleOperatorSubsystemCompletionReadiness:
    oracle_operator_subsystem_completion_readiness_id: str
    source_presentation_subsystem_completion_certification_id: str
    source_presentation_subsystem_completion_certification_hash: str
    source_publication_completion_attestation_id: str
    source_publication_completion_attestation_hash: str
    source_publication_result_certification_id: str
    source_publication_result_certification_hash: str
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
    published_presentation_artifact_type: str
    published_presentation_format: str
    presentation_certification_type: str
    presentation_freeze_record_type: str
    readiness_type: str
    readiness_record_type: str
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
    readiness_record_id: str
    readiness_record_payload: Mapping[str, Any]
    readiness_record_payload_hash: str
    presentation_certification_identity_verified: bool
    presentation_certification_hash_verified: bool
    presentation_certification_status_verified: bool
    presentation_certification_type_verified: bool
    presentation_freeze_record_type_verified: bool
    presentation_freeze_record_identity_verified: bool
    presentation_freeze_record_payload_hash_verified: bool
    operator_namespace_verified: bool
    presentation_namespace_verified: bool
    query_boundary_verified: bool
    research_response_boundary_verified: bool
    session_boundary_verified: bool
    console_boundary_verified: bool
    presentation_boundary_verified: bool
    publication_chain_completion_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    deterministic_readiness_verified: bool
    immutable_readiness_record_verified: bool
    read_only_operator_subsystem_verified: bool
    operator_presentation_subsystem_completion_certified: bool
    operator_presentation_subsystem_frozen: bool
    operator_query_boundary_complete: bool
    operator_research_response_boundary_complete: bool
    operator_session_boundary_complete: bool
    operator_console_boundary_complete: bool
    operator_presentation_boundary_complete: bool
    oracle_operator_subsystem_completion_ready: bool
    oracle_operator_subsystem_completion_certified: bool
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
    readiness_status: str
    oracle_operator_subsystem_completion_readiness_hash: str


class OracleOperatorSubsystemCompletionReadinessGate:
    @staticmethod
    def _verify(
        certification: OracleOperatorPresentationSubsystemCompletionCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorPresentationSubsystemCompletionCertification,
        ):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "source must be canonical OOP-045 presentation completion certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop(
            "oracle_operator_presentation_subsystem_completion_certification_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 certification hash mismatch"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 certification status mismatch"
            )
        if certification.certification_type != EXPECTED_CERTIFICATION_TYPE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 certification type mismatch"
            )
        if certification.freeze_record_type != EXPECTED_FREEZE_RECORD_TYPE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 freeze record type mismatch"
            )
        if certification.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "operator namespace mismatch"
            )
        if certification.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(certification.freeze_record_id):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record id invalid"
            )
        if not _valid_sha256(certification.freeze_record_payload_hash):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record payload hash invalid"
            )
        if stable_hash(certification.freeze_record_payload) != certification.freeze_record_payload_hash:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record payload hash mismatch"
            )

        freeze_payload = certification.freeze_record_payload
        if freeze_payload.get("freeze_record_id") != certification.freeze_record_id:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze record identity mismatch"
            )
        if freeze_payload.get("presentation_namespace") != certification.presentation_namespace:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze namespace mismatch"
            )
        if freeze_payload.get("published_presentation_id") != certification.published_presentation_id:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "published presentation identity mismatch"
            )
        if freeze_payload.get("published_presentation_payload_hash") != certification.published_presentation_payload_hash:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "published presentation payload hash mismatch"
            )

        required_freeze_state = (
            freeze_payload.get("publication_chain_complete") is True,
            freeze_payload.get("presentation_subsystem_complete") is True,
            freeze_payload.get("presentation_subsystem_frozen") is True,
            freeze_payload.get("further_presentation_certification_required") is False,
            freeze_payload.get("read_only") is True,
            freeze_payload.get("qseries_handoff_disabled") is True,
            freeze_payload.get("qseries_execution_disabled") is True,
            freeze_payload.get("orders_disabled") is True,
            freeze_payload.get("funds_movement_disabled") is True,
            freeze_payload.get("portfolio_mutation_disabled") is True,
        )
        if not all(required_freeze_state):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation freeze state mismatch"
            )

        required = (
            certification.attestation_identity_verified,
            certification.attestation_hash_verified,
            certification.attestation_status_verified,
            certification.attestation_type_verified,
            certification.completion_record_type_verified,
            certification.completion_record_identity_verified,
            certification.completion_record_payload_hash_verified,
            certification.published_presentation_identity_verified,
            certification.published_presentation_payload_hash_verified,
            certification.publication_chain_completion_verified,
            certification.complete_lineage_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.deterministic_certification_verified,
            certification.immutable_freeze_record_verified,
            certification.read_only_subsystem_verified,
            certification.publication_result_certified,
            certification.publication_completion_attested,
            certification.presentation_publication_chain_complete,
            certification.operator_presentation_subsystem_completion_ready,
            certification.operator_presentation_subsystem_completion_certified,
            certification.operator_presentation_subsystem_frozen,
        )
        if not all(required):
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "OOP-045 presentation completion certification incomplete"
            )
        if certification.further_presentation_certification_required:
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "presentation subsystem still requires certification"
            )

        forbidden = (
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
            raise OracleOperatorSubsystemCompletionReadinessInvariantError(
                "forbidden downstream activity detected"
            )

    def evaluate(
        self,
        *,
        certification: OracleOperatorPresentationSubsystemCompletionCertification,
    ) -> OracleOperatorSubsystemCompletionReadiness:
        self._verify(certification)

        readiness_record_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_presentation_certification_id": certification.oracle_operator_presentation_subsystem_completion_certification_id,
                "source_presentation_certification_hash": certification.oracle_operator_presentation_subsystem_completion_certification_hash,
                "presentation_freeze_record_id": certification.freeze_record_id,
                "presentation_freeze_record_payload_hash": certification.freeze_record_payload_hash,
                "readiness_record_type": READINESS_RECORD_TYPE,
            }
        )

        readiness_record_payload = {
            "readiness_record_id": readiness_record_id,
            "readiness_record_type": READINESS_RECORD_TYPE,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": certification.research_response_namespace,
            "session_namespace": certification.session_namespace,
            "console_namespace": certification.console_namespace,
            "presentation_namespace": certification.presentation_namespace,
            "presentation_subsystem_completion_certification_id": certification.oracle_operator_presentation_subsystem_completion_certification_id,
            "presentation_subsystem_completion_certification_hash": certification.oracle_operator_presentation_subsystem_completion_certification_hash,
            "presentation_freeze_record_id": certification.freeze_record_id,
            "presentation_freeze_record_payload_hash": certification.freeze_record_payload_hash,
            "published_presentation_id": certification.published_presentation_id,
            "published_presentation_payload_hash": certification.published_presentation_payload_hash,
            "query_boundary_complete": True,
            "research_response_boundary_complete": True,
            "session_boundary_complete": True,
            "console_boundary_complete": True,
            "presentation_boundary_complete": True,
            "operator_subsystem_completion_ready": True,
            "operator_subsystem_completion_certified": False,
            "further_operator_builds_required": True,
            "read_only": True,
            "qseries_handoff_disabled": True,
            "qseries_execution_disabled": True,
            "orders_disabled": True,
            "funds_movement_disabled": True,
            "portfolio_mutation_disabled": True,
        }
        readiness_record_payload_hash = stable_hash(readiness_record_payload)

        readiness_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "readiness_record_id": readiness_record_id,
                "readiness_record_payload_hash": readiness_record_payload_hash,
                "readiness_type": READINESS_TYPE,
            }
        )

        body = {
            "oracle_operator_subsystem_completion_readiness_id": readiness_id,
            "source_presentation_subsystem_completion_certification_id": certification.oracle_operator_presentation_subsystem_completion_certification_id,
            "source_presentation_subsystem_completion_certification_hash": certification.oracle_operator_presentation_subsystem_completion_certification_hash,
            "source_publication_completion_attestation_id": certification.source_publication_completion_attestation_id,
            "source_publication_completion_attestation_hash": certification.source_publication_completion_attestation_hash,
            "source_publication_result_certification_id": certification.source_publication_result_certification_id,
            "source_publication_result_certification_hash": certification.source_publication_result_certification_hash,
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
            "published_presentation_artifact_type": certification.published_presentation_artifact_type,
            "published_presentation_format": certification.published_presentation_format,
            "presentation_certification_type": certification.certification_type,
            "presentation_freeze_record_type": certification.freeze_record_type,
            "readiness_type": READINESS_TYPE,
            "readiness_record_type": READINESS_RECORD_TYPE,
            "research_response_id": certification.research_response_id,
            "research_response_payload_hash": certification.research_response_payload_hash,
            "research_response_item_count": certification.research_response_item_count,
            "operator_session_id": certification.operator_session_id,
            "operator_session_payload_hash": certification.operator_session_payload_hash,
            "operator_console_id": certification.operator_console_id,
            "operator_console_payload_hash": certification.operator_console_payload_hash,
            "rendered_console_id": certification.rendered_console_id,
            "rendered_console_payload_hash": certification.rendered_console_payload_hash,
            "rendered_presentation_id": certification.rendered_presentation_id,
            "rendered_presentation_payload_hash": certification.rendered_presentation_payload_hash,
            "published_presentation_id": certification.published_presentation_id,
            "published_presentation_payload_hash": certification.published_presentation_payload_hash,
            "presentation_freeze_record_id": certification.freeze_record_id,
            "presentation_freeze_record_payload_hash": certification.freeze_record_payload_hash,
            "readiness_record_id": readiness_record_id,
            "readiness_record_payload": readiness_record_payload,
            "readiness_record_payload_hash": readiness_record_payload_hash,
            "presentation_certification_identity_verified": True,
            "presentation_certification_hash_verified": True,
            "presentation_certification_status_verified": True,
            "presentation_certification_type_verified": True,
            "presentation_freeze_record_type_verified": True,
            "presentation_freeze_record_identity_verified": True,
            "presentation_freeze_record_payload_hash_verified": True,
            "operator_namespace_verified": True,
            "presentation_namespace_verified": True,
            "query_boundary_verified": True,
            "research_response_boundary_verified": True,
            "session_boundary_verified": True,
            "console_boundary_verified": True,
            "presentation_boundary_verified": True,
            "publication_chain_completion_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "deterministic_readiness_verified": True,
            "immutable_readiness_record_verified": True,
            "read_only_operator_subsystem_verified": True,
            "operator_presentation_subsystem_completion_certified": True,
            "operator_presentation_subsystem_frozen": True,
            "operator_query_boundary_complete": True,
            "operator_research_response_boundary_complete": True,
            "operator_session_boundary_complete": True,
            "operator_console_boundary_complete": True,
            "operator_presentation_boundary_complete": True,
            "oracle_operator_subsystem_completion_ready": True,
            "oracle_operator_subsystem_completion_certified": False,
            "further_operator_builds_required": True,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "readiness_status": READINESS_STATUS,
        }

        return OracleOperatorSubsystemCompletionReadiness(
            **body,
            oracle_operator_subsystem_completion_readiness_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "READINESS_STATUS",
    "READINESS_TYPE",
    "READINESS_RECORD_TYPE",
    "OracleOperatorSubsystemCompletionReadiness",
    "OracleOperatorSubsystemCompletionReadinessGate",
    "OracleOperatorSubsystemCompletionReadinessInvariantError",
    "stable_hash",
]
