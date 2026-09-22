from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)

BUILD_ID = "OI-062"
OI_062_REVISION = "OI_062_MULTI_SUBJECT_CONVERSATION_COORDINATOR_V1"

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


@dataclass(frozen=True, slots=True)
class MultiSubjectConversationState:
    session_id: str
    active_subject_hint: str | None
    subject_hints: tuple[str, ...]
    subject_turn_counts: tuple[tuple[str, int], ...]
    state_hash: str
    read_only: bool


class MultiSubjectConversationCoordinator:
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
        context: ExplanationConversationContext,
    ) -> MultiSubjectConversationState:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        counts = {}

        for turn in context.turns:
            subject = turn.subject_hint
            counts[subject] = counts.get(subject, 0) + 1

        subjects = tuple(sorted(counts))

        subject_turn_counts = tuple(
            (subject, counts[subject])
            for subject in subjects
        )

        body = {
            "session_id": context.session_id,
            "active_subject_hint": (
                context.latest_subject_hint
            ),
            "subject_hints": subjects,
            "subject_turn_counts": subject_turn_counts,
            "read_only": True,
        }

        return MultiSubjectConversationState(
            session_id=context.session_id,
            active_subject_hint=(
                context.latest_subject_hint
            ),
            subject_hints=subjects,
            subject_turn_counts=subject_turn_counts,
            state_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_multi_subject_conversation_coordinator() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-062 must remain read-only")

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
        raise AssertionError(
            "OI-062 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_062_REVISION",
    "MultiSubjectConversationState",
    "MultiSubjectConversationCoordinator",
    "verify_multi_subject_conversation_coordinator",
]
