from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_completion_attestation_gate import (
    ATTESTATION_STATUS as OOP_044_ATTESTATION_STATUS,
    ATTESTATION_TYPE as OOP_044_ATTESTATION_TYPE,
    COMPLETION_RECORD_TYPE as OOP_044_COMPLETION_RECORD_TYPE,
    OracleOperatorPresentationPublicationCompletionAttestation,
)

SCHEMA_VERSION = "OOP-045"
ENGINE_ID = "OOP-045"
POLICY_ID = "oracle.operator.presentation-subsystem-completion-certification-gate.v1"
CERTIFICATION_STATUS = "oracle_operator_presentation_subsystem_completion_certified"
CERTIFICATION_TYPE = "terminal_immutable_oracle_operator_presentation_subsystem_completion_certification"
FREEZE_RECORD_TYPE = "oracle_operator_presentation_subsystem_terminal_freeze_record"

EXPECTED_ATTESTATION_STATUS = OOP_044_ATTESTATION_STATUS
EXPECTED_ATTESTATION_TYPE = OOP_044_ATTESTATION_TYPE
EXPECTED_COMPLETION_RECORD_TYPE = OOP_044_COMPLETION_RECORD_TYPE
EXPECTED_PRESENTATION_NAMESPACE = "qseries_v2.oracle_operator.presentation"


class OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(RuntimeError):
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
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
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
class OracleOperatorPresentationSubsystemCompletionCertification:
    oracle_operator_presentation_subsystem_completion_certification_id: str
    source_publication_completion_attestation_id: str
    source_publication_completion_attestation_hash: str
    source_publication_result_certification_id: str
    source_publication_result_certification_hash: str
    source_publication_execution_id: str
    source_publication_execution_hash: str
    source_publication_consumption_id: str
    source_publication_consumption_hash: str
    source_publication_authorization_id: str
    source_publication_authorization_hash: str
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
    attestation_type: str
    completion_record_type: str
    certification_type: str
    freeze_record_type: str
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
    completion_record_id: str
    completion_record_payload_hash: str
    freeze_record_id: str
    freeze_record_payload: Mapping[str, Any]
    freeze_record_payload_hash: str
    attestation_identity_verified: bool
    attestation_hash_verified: bool
    attestation_status_verified: bool
    attestation_type_verified: bool
    completion_record_type_verified: bool
    completion_record_identity_verified: bool
    completion_record_payload_hash_verified: bool
    published_presentation_identity_verified: bool
    published_presentation_payload_hash_verified: bool
    publication_chain_completion_verified: bool
    complete_lineage_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    deterministic_certification_verified: bool
    immutable_freeze_record_verified: bool
    read_only_subsystem_verified: bool
    publication_result_certified: bool
    publication_completion_attested: bool
    presentation_publication_chain_complete: bool
    operator_presentation_subsystem_completion_ready: bool
    operator_presentation_subsystem_completion_certified: bool
    operator_presentation_subsystem_frozen: bool
    further_presentation_certification_required: bool
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
    oracle_operator_presentation_subsystem_completion_certification_hash: str


class OracleOperatorPresentationSubsystemCompletionCertificationGate:
    @staticmethod
    def _verify(
        attestation: OracleOperatorPresentationPublicationCompletionAttestation,
    ) -> None:
        if not isinstance(
            attestation,
            OracleOperatorPresentationPublicationCompletionAttestation,
        ):
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "source must be canonical OOP-044 completion attestation"
            )

        body = asdict(attestation)
        supplied_hash = body.pop(
            "operator_presentation_publication_completion_attestation_hash",
            None,
        )
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "OOP-044 attestation hash mismatch"
            )

        if attestation.attestation_status != EXPECTED_ATTESTATION_STATUS:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "OOP-044 attestation status mismatch"
            )
        if attestation.attestation_type != EXPECTED_ATTESTATION_TYPE:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "OOP-044 attestation type mismatch"
            )
        if attestation.completion_record_type != EXPECTED_COMPLETION_RECORD_TYPE:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "OOP-044 completion record type mismatch"
            )
        if attestation.presentation_namespace != EXPECTED_PRESENTATION_NAMESPACE:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "presentation namespace mismatch"
            )

        if not _valid_sha256(attestation.completion_record_id):
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "completion record id invalid"
            )
        if not _valid_sha256(attestation.completion_record_payload_hash):
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "completion record payload hash invalid"
            )
        if stable_hash(attestation.completion_record_payload) != attestation.completion_record_payload_hash:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "completion record payload hash mismatch"
            )

        payload = attestation.completion_record_payload
        if payload.get("completion_record_id") != attestation.completion_record_id:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "completion record identity mismatch"
            )
        if payload.get("published_presentation_id") != attestation.published_presentation_id:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "published presentation identity mismatch"
            )
        if payload.get("published_presentation_payload_hash") != attestation.published_presentation_payload_hash:
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "published presentation payload hash mismatch"
            )

        boundaries = (
            payload.get("publication_complete") is True,
            payload.get("presentation_publication_chain_complete") is True,
            payload.get("read_only") is True,
            payload.get("qseries_handoff_disabled") is True,
            payload.get("qseries_execution_disabled") is True,
            payload.get("orders_disabled") is True,
            payload.get("funds_movement_disabled") is True,
            payload.get("portfolio_mutation_disabled") is True,
        )
        if not all(boundaries):
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "completion record safety boundary mismatch"
            )

        required = (
            attestation.certification_identity_verified,
            attestation.certification_hash_verified,
            attestation.certification_status_verified,
            attestation.certification_type_verified,
            attestation.published_presentation_identity_verified,
            attestation.published_presentation_payload_hash_verified,
            attestation.published_presentation_artifact_type_verified,
            attestation.published_presentation_format_verified,
            attestation.publication_completion_verified,
            attestation.complete_lineage_verified,
            attestation.frozen_scope_verified,
            attestation.frozen_scope_preserved,
            attestation.deterministic_attestation_verified,
            attestation.immutable_completion_record_verified,
            attestation.read_only_completion_verified,
            attestation.publication_result_certified,
            attestation.publication_completion_attested,
            attestation.presentation_publication_chain_complete,
            attestation.operator_presentation_subsystem_completion_ready,
        )
        if not all(required):
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "OOP-044 completion attestation incomplete"
            )

        forbidden = (
            attestation.qseries_handoff_allowed,
            attestation.qseries_execution_allowed,
            attestation.qseries_execution_performed,
            attestation.order_creation_allowed,
            attestation.order_creation_performed,
            attestation.funds_movement_allowed,
            attestation.funds_movement_performed,
            attestation.portfolio_mutation_allowed,
            attestation.portfolio_mutation_performed,
        )
        if any(forbidden):
            raise OracleOperatorPresentationSubsystemCompletionCertificationInvariantError(
                "forbidden downstream activity detected"
            )

    def certify(
        self,
        *,
        attestation: OracleOperatorPresentationPublicationCompletionAttestation,
    ) -> OracleOperatorPresentationSubsystemCompletionCertification:
        self._verify(attestation)

        freeze_record_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_attestation_id": attestation.operator_presentation_publication_completion_attestation_id,
                "source_attestation_hash": attestation.operator_presentation_publication_completion_attestation_hash,
                "completion_record_id": attestation.completion_record_id,
                "completion_record_payload_hash": attestation.completion_record_payload_hash,
                "freeze_record_type": FREEZE_RECORD_TYPE,
            }
        )

        freeze_record_payload = {
            "freeze_record_id": freeze_record_id,
            "freeze_record_type": FREEZE_RECORD_TYPE,
            "presentation_namespace": attestation.presentation_namespace,
            "publication_completion_attestation_id": attestation.operator_presentation_publication_completion_attestation_id,
            "publication_completion_attestation_hash": attestation.operator_presentation_publication_completion_attestation_hash,
            "completion_record_id": attestation.completion_record_id,
            "completion_record_payload_hash": attestation.completion_record_payload_hash,
            "published_presentation_id": attestation.published_presentation_id,
            "published_presentation_payload_hash": attestation.published_presentation_payload_hash,
            "publication_chain_complete": True,
            "presentation_subsystem_complete": True,
            "presentation_subsystem_frozen": True,
            "further_presentation_certification_required": False,
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
            "oracle_operator_presentation_subsystem_completion_certification_id": certification_id,
            "source_publication_completion_attestation_id": attestation.operator_presentation_publication_completion_attestation_id,
            "source_publication_completion_attestation_hash": attestation.operator_presentation_publication_completion_attestation_hash,
            "source_publication_result_certification_id": attestation.source_operator_presentation_publication_result_certification_id,
            "source_publication_result_certification_hash": attestation.source_operator_presentation_publication_result_certification_hash,
            "source_publication_execution_id": attestation.source_operator_presentation_publication_execution_id,
            "source_publication_execution_hash": attestation.source_operator_presentation_publication_execution_hash,
            "source_publication_consumption_id": attestation.source_operator_presentation_publication_consumption_id,
            "source_publication_consumption_hash": attestation.source_operator_presentation_publication_consumption_hash,
            "source_publication_authorization_id": attestation.source_operator_presentation_publication_authorization_id,
            "source_publication_authorization_hash": attestation.source_operator_presentation_publication_authorization_hash,
            "operator_namespace": attestation.operator_namespace,
            "query_namespace": attestation.query_namespace,
            "research_response_namespace": attestation.research_response_namespace,
            "session_namespace": attestation.session_namespace,
            "console_namespace": attestation.console_namespace,
            "presentation_namespace": attestation.presentation_namespace,
            "consumer_id": attestation.consumer_id,
            "query_text": attestation.query_text,
            "query_mode": attestation.query_mode,
            "projection": attestation.projection,
            "time_scope": attestation.time_scope,
            "sort_order": attestation.sort_order,
            "result_limit": attestation.result_limit,
            "requested_tags": tuple(attestation.requested_tags),
            "published_presentation_artifact_type": attestation.published_presentation_artifact_type,
            "published_presentation_format": attestation.published_presentation_format,
            "attestation_type": attestation.attestation_type,
            "completion_record_type": attestation.completion_record_type,
            "certification_type": CERTIFICATION_TYPE,
            "freeze_record_type": FREEZE_RECORD_TYPE,
            "research_response_id": attestation.research_response_id,
            "research_response_payload_hash": attestation.research_response_payload_hash,
            "research_response_item_count": attestation.research_response_item_count,
            "operator_session_id": attestation.operator_session_id,
            "operator_session_payload_hash": attestation.operator_session_payload_hash,
            "operator_console_id": attestation.operator_console_id,
            "operator_console_payload_hash": attestation.operator_console_payload_hash,
            "rendered_console_id": attestation.rendered_console_id,
            "rendered_console_payload_hash": attestation.rendered_console_payload_hash,
            "rendered_presentation_id": attestation.rendered_presentation_id,
            "rendered_presentation_payload_hash": attestation.rendered_presentation_payload_hash,
            "published_presentation_id": attestation.published_presentation_id,
            "published_presentation_payload_hash": attestation.published_presentation_payload_hash,
            "completion_record_id": attestation.completion_record_id,
            "completion_record_payload_hash": attestation.completion_record_payload_hash,
            "freeze_record_id": freeze_record_id,
            "freeze_record_payload": freeze_record_payload,
            "freeze_record_payload_hash": freeze_record_payload_hash,
            "attestation_identity_verified": True,
            "attestation_hash_verified": True,
            "attestation_status_verified": True,
            "attestation_type_verified": True,
            "completion_record_type_verified": True,
            "completion_record_identity_verified": True,
            "completion_record_payload_hash_verified": True,
            "published_presentation_identity_verified": True,
            "published_presentation_payload_hash_verified": True,
            "publication_chain_completion_verified": True,
            "complete_lineage_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "deterministic_certification_verified": True,
            "immutable_freeze_record_verified": True,
            "read_only_subsystem_verified": True,
            "publication_result_certified": True,
            "publication_completion_attested": True,
            "presentation_publication_chain_complete": True,
            "operator_presentation_subsystem_completion_ready": True,
            "operator_presentation_subsystem_completion_certified": True,
            "operator_presentation_subsystem_frozen": True,
            "further_presentation_certification_required": False,
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

        return OracleOperatorPresentationSubsystemCompletionCertification(
            **body,
            oracle_operator_presentation_subsystem_completion_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_STATUS",
    "CERTIFICATION_TYPE",
    "FREEZE_RECORD_TYPE",
    "OracleOperatorPresentationSubsystemCompletionCertification",
    "OracleOperatorPresentationSubsystemCompletionCertificationGate",
    "OracleOperatorPresentationSubsystemCompletionCertificationInvariantError",
    "stable_hash",
]
