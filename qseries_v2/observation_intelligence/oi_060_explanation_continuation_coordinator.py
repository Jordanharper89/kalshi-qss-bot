from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)
from .oi_058_explanation_followup_reference_resolution import (
    ExplanationFollowUpReferenceResolution,
)
from .oi_059_explanation_session_delta_projection import (
    ExplanationSessionDelta,
)

BUILD_ID = "OI-060"
OI_060_REVISION = "OI_060_EXPLANATION_CONTINUATION_COORDINATOR_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
TERMINAL_MUTATION_ALLOWED = False

CONTINUE_RESOLVED = "continue_resolved"
CONTINUE_UNRESOLVED = "continue_unresolved"


@dataclass(frozen=True, slots=True)
class OracleExplanationContinuation:
    session_id: str
    continuation_status: str
    resolved_subject_hint: str | None
    resolved_query_id: str | None
    session_change_type: str
    prior_turn_count: int
    continuation_hash: str
    read_only: bool


class OracleExplanationContinuationCoordinator:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    causal_claim_allowed = False
    terminal_mutation_allowed = False

    def coordinate(
        self,
        *,
        context: ExplanationConversationContext,
        reference: ExplanationFollowUpReferenceResolution,
        delta: ExplanationSessionDelta,
    ) -> OracleExplanationContinuation:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        if not isinstance(
            reference,
            ExplanationFollowUpReferenceResolution,
        ):
            raise TypeError(
                "reference must be ExplanationFollowUpReferenceResolution"
            )

        if not isinstance(
            delta,
            ExplanationSessionDelta,
        ):
            raise TypeError(
                "delta must be ExplanationSessionDelta"
            )

        if not (
            context.session_id
            == reference.session_id
            == delta.session_id
        ):
            raise ValueError(
                "context/reference/delta session_id mismatch"
            )

        resolved = (
            reference.resolved_subject_hint is not None
            or reference.resolved_query_id is not None
        )

        continuation_status = (
            CONTINUE_RESOLVED
            if resolved
            else CONTINUE_UNRESOLVED
        )

        body = {
            "session_id": context.session_id,
            "continuation_status": continuation_status,
            "resolved_subject_hint": (
                reference.resolved_subject_hint
            ),
            "resolved_query_id": (
                reference.resolved_query_id
            ),
            "session_change_type": delta.change_type,
            "prior_turn_count": context.turn_count,
            "read_only": True,
        }

        return OracleExplanationContinuation(
            session_id=context.session_id,
            continuation_status=continuation_status,
            resolved_subject_hint=(
                reference.resolved_subject_hint
            ),
            resolved_query_id=(
                reference.resolved_query_id
            ),
            session_change_type=delta.change_type,
            prior_turn_count=context.turn_count,
            continuation_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_continuation_coordinator() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-060 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError("OI-060 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_060_REVISION",
    "CONTINUE_RESOLVED",
    "CONTINUE_UNRESOLVED",
    "OracleExplanationContinuation",
    "OracleExplanationContinuationCoordinator",
    "verify_explanation_continuation_coordinator",
]
