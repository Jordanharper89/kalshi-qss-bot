from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_056_explanation_conversation_context import (
    ExplanationConversationContext,
)

BUILD_ID = "OI-058"
OI_058_REVISION = "OI_058_EXPLANATION_FOLLOWUP_REFERENCE_RESOLUTION_V1"

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

REFERENCE_CURRENT_SUBJECT = "current_subject"
REFERENCE_CURRENT_QUERY = "current_query"
REFERENCE_UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ExplanationFollowUpReferenceResolution:
    session_id: str
    raw_followup: str
    resolved_subject_hint: str | None
    resolved_query_id: str | None
    resolution_type: str
    resolution_hash: str
    read_only: bool


class ExplanationFollowUpReferenceResolver:
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

    _SUBJECT_REFERENCE_TOKENS = (
        "that",
        "that market",
        "that move",
        "that edge",
        "it",
        "this",
        "this market",
        "this move",
        "this edge",
    )

    def resolve(
        self,
        *,
        context: ExplanationConversationContext,
        raw_followup: str,
    ) -> ExplanationFollowUpReferenceResolution:
        if not isinstance(
            context,
            ExplanationConversationContext,
        ):
            raise TypeError(
                "context must be ExplanationConversationContext"
            )

        text = " ".join(str(raw_followup).strip().split())
        if not text:
            raise ValueError("raw_followup must not be empty")

        lower = text.lower()

        resolved_subject = None
        resolved_query = None
        resolution_type = REFERENCE_UNRESOLVED

        if context.turn_count > 0:
            if any(
                token in lower
                for token in self._SUBJECT_REFERENCE_TOKENS
            ):
                resolved_subject = context.latest_subject_hint
                resolved_query = context.latest_query_id
                resolution_type = REFERENCE_CURRENT_SUBJECT
            elif (
                "previous question" in lower
                or "last question" in lower
                or "that question" in lower
            ):
                resolved_subject = context.latest_subject_hint
                resolved_query = context.latest_query_id
                resolution_type = REFERENCE_CURRENT_QUERY

        body = {
            "session_id": context.session_id,
            "raw_followup": text,
            "resolved_subject_hint": resolved_subject,
            "resolved_query_id": resolved_query,
            "resolution_type": resolution_type,
            "read_only": True,
        }

        return ExplanationFollowUpReferenceResolution(
            session_id=context.session_id,
            raw_followup=text,
            resolved_subject_hint=resolved_subject,
            resolved_query_id=resolved_query,
            resolution_type=resolution_type,
            resolution_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_followup_reference_resolution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-058 must remain read-only")

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
        raise AssertionError("OI-058 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_058_REVISION",
    "REFERENCE_CURRENT_SUBJECT",
    "REFERENCE_CURRENT_QUERY",
    "REFERENCE_UNRESOLVED",
    "ExplanationFollowUpReferenceResolution",
    "ExplanationFollowUpReferenceResolver",
    "verify_explanation_followup_reference_resolution",
]
