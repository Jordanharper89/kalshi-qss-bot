from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)

BUILD_ID = "OI-059"
OI_059_REVISION = "OI_059_EXPLANATION_SESSION_DELTA_PROJECTION_V1"

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

CHANGE_NONE = "none"
CHANGE_QUERY = "query_changed"
CHANGE_SUBJECT = "subject_changed"
CHANGE_COMPLETENESS = "completeness_changed"
CHANGE_MULTIPLE = "multiple_changes"


@dataclass(frozen=True, slots=True)
class ExplanationSessionDelta:
    session_id: str
    previous_turn_number: int | None
    current_turn_number: int | None
    query_changed: bool
    subject_changed: bool
    completeness_changed: bool
    change_type: str
    delta_hash: str
    read_only: bool


class ExplanationSessionDeltaProjector:
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

    def project(
        self,
        context: ExplanationConversationContext,
    ) -> ExplanationSessionDelta:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        previous = (
            context.turns[-2]
            if context.turn_count >= 2
            else None
        )
        current = (
            context.turns[-1]
            if context.turn_count >= 1
            else None
        )

        if previous is None or current is None:
            query_changed = False
            subject_changed = False
            completeness_changed = False
            change_type = CHANGE_NONE
        else:
            query_changed = previous.query_id != current.query_id
            subject_changed = (
                previous.subject_hint != current.subject_hint
            )
            completeness_changed = (
                previous.completeness_status
                != current.completeness_status
            )

            changed_count = sum(
                (
                    query_changed,
                    subject_changed,
                    completeness_changed,
                )
            )

            if changed_count == 0:
                change_type = CHANGE_NONE
            elif changed_count > 1:
                change_type = CHANGE_MULTIPLE
            elif query_changed:
                change_type = CHANGE_QUERY
            elif subject_changed:
                change_type = CHANGE_SUBJECT
            else:
                change_type = CHANGE_COMPLETENESS

        body = {
            "session_id": context.session_id,
            "previous_turn_number": (
                previous.turn_number if previous else None
            ),
            "current_turn_number": (
                current.turn_number if current else None
            ),
            "query_changed": query_changed,
            "subject_changed": subject_changed,
            "completeness_changed": completeness_changed,
            "change_type": change_type,
            "read_only": True,
        }

        return ExplanationSessionDelta(
            session_id=context.session_id,
            previous_turn_number=(
                previous.turn_number if previous else None
            ),
            current_turn_number=(
                current.turn_number if current else None
            ),
            query_changed=query_changed,
            subject_changed=subject_changed,
            completeness_changed=completeness_changed,
            change_type=change_type,
            delta_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_session_delta_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-059 must remain read-only")

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
        raise AssertionError("OI-059 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_059_REVISION",
    "CHANGE_NONE",
    "CHANGE_QUERY",
    "CHANGE_SUBJECT",
    "CHANGE_COMPLETENESS",
    "CHANGE_MULTIPLE",
    "ExplanationSessionDelta",
    "ExplanationSessionDeltaProjector",
    "verify_explanation_session_delta_projection",
]
