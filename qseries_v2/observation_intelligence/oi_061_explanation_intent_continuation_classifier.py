from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_058_explanation_followup_reference_resolution import (
    ExplanationFollowUpReferenceResolution,
)
from .oi_060_explanation_continuation_coordinator import (
    OracleExplanationContinuation,
)

BUILD_ID = "OI-061"
OI_061_REVISION = "OI_061_EXPLANATION_INTENT_CONTINUATION_CLASSIFIER_V1"

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

INTENT_CONTINUE = "continue_explanation"
INTENT_MORE_EVIDENCE = "more_evidence"
INTENT_CONTRADICTION = "contradiction"
INTENT_TIMELINE = "timeline"
INTENT_NEW_SUBJECT = "new_subject"
INTENT_UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ExplanationContinuationIntent:
    session_id: str
    raw_followup: str
    intent: str
    resolved_subject_hint: str | None
    resolved_query_id: str | None
    intent_hash: str
    read_only: bool


class ExplanationIntentContinuationClassifier:
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

    def classify(
        self,
        *,
        reference: ExplanationFollowUpReferenceResolution,
        continuation: OracleExplanationContinuation,
    ) -> ExplanationContinuationIntent:
        if not isinstance(
            reference,
            ExplanationFollowUpReferenceResolution,
        ):
            raise TypeError(
                "reference must be ExplanationFollowUpReferenceResolution"
            )

        if not isinstance(
            continuation,
            OracleExplanationContinuation,
        ):
            raise TypeError(
                "continuation must be OracleExplanationContinuation"
            )

        if reference.session_id != continuation.session_id:
            raise ValueError(
                "reference/continuation session_id mismatch"
            )

        text = reference.raw_followup.lower()

        if continuation.continuation_status == "continue_unresolved":
            intent = INTENT_UNRESOLVED
        elif any(
            token in text
            for token in (
                "contradict",
                "contradiction",
                "conflict",
                "disagree",
            )
        ):
            intent = INTENT_CONTRADICTION
        elif any(
            token in text
            for token in (
                "timeline",
                "when did",
                "what changed",
                "since",
            )
        ):
            intent = INTENT_TIMELINE
        elif any(
            token in text
            for token in (
                "evidence",
                "support",
                "sources",
                "show me more",
            )
        ):
            intent = INTENT_MORE_EVIDENCE
        elif any(
            token in text
            for token in (
                "another market",
                "different market",
                "different subject",
                "new subject",
            )
        ):
            intent = INTENT_NEW_SUBJECT
        else:
            intent = INTENT_CONTINUE

        body = {
            "session_id": reference.session_id,
            "raw_followup": reference.raw_followup,
            "intent": intent,
            "resolved_subject_hint": (
                reference.resolved_subject_hint
            ),
            "resolved_query_id": (
                reference.resolved_query_id
            ),
            "read_only": True,
        }

        return ExplanationContinuationIntent(
            session_id=reference.session_id,
            raw_followup=reference.raw_followup,
            intent=intent,
            resolved_subject_hint=(
                reference.resolved_subject_hint
            ),
            resolved_query_id=(
                reference.resolved_query_id
            ),
            intent_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_intent_continuation_classifier() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-061 must remain read-only")

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
            "OI-061 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_061_REVISION",
    "INTENT_CONTINUE",
    "INTENT_MORE_EVIDENCE",
    "INTENT_CONTRADICTION",
    "INTENT_TIMELINE",
    "INTENT_NEW_SUBJECT",
    "INTENT_UNRESOLVED",
    "ExplanationContinuationIntent",
    "ExplanationIntentContinuationClassifier",
    "verify_explanation_intent_continuation_classifier",
]
