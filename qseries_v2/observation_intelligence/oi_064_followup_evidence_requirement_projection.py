from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_061_explanation_intent_continuation_classifier import (
    ExplanationContinuationIntent,
    INTENT_CONTINUE,
    INTENT_MORE_EVIDENCE,
    INTENT_CONTRADICTION,
    INTENT_TIMELINE,
    INTENT_NEW_SUBJECT,
    INTENT_UNRESOLVED,
)

BUILD_ID = "OI-064"
OI_064_REVISION = "OI_064_FOLLOWUP_EVIDENCE_REQUIREMENT_PROJECTION_V1"

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

NEED_CURRENT_EVIDENCE = "current_evidence"
NEED_ADDITIONAL_EVIDENCE = "additional_evidence"
NEED_CONTRADICTORY_EVIDENCE = "contradictory_evidence"
NEED_TEMPORAL_EVIDENCE = "temporal_evidence"
NEED_SUBJECT_DISCOVERY = "subject_discovery"


@dataclass(frozen=True, slots=True)
class FollowUpEvidenceRequirement:
    requirement_id: str
    subject_hint: str | None
    need_type: str
    required: bool
    reason: str
    requirement_hash: str


@dataclass(frozen=True, slots=True)
class FollowUpEvidenceRequirementProjection:
    session_id: str
    intent: str
    subject_hint: str | None
    requirements: tuple[FollowUpEvidenceRequirement, ...]
    projection_status: str
    projection_hash: str
    read_only: bool


class FollowUpEvidenceRequirementProjector:
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

    def project(
        self,
        intent: ExplanationContinuationIntent,
    ) -> FollowUpEvidenceRequirementProjection:
        if not isinstance(
            intent,
            ExplanationContinuationIntent,
        ):
            raise TypeError(
                "intent must be ExplanationContinuationIntent"
            )

        specs = ()

        if intent.intent == INTENT_MORE_EVIDENCE:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "preserve_current_support",
                ),
                (
                    NEED_ADDITIONAL_EVIDENCE,
                    True,
                    "expand_evidence_support",
                ),
            )
        elif intent.intent == INTENT_CONTRADICTION:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "preserve_current_support",
                ),
                (
                    NEED_CONTRADICTORY_EVIDENCE,
                    True,
                    "inspect_conflicting_evidence",
                ),
            )
        elif intent.intent == INTENT_TIMELINE:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "preserve_current_support",
                ),
                (
                    NEED_TEMPORAL_EVIDENCE,
                    True,
                    "inspect_change_over_time",
                ),
            )
        elif intent.intent == INTENT_CONTINUE:
            specs = (
                (
                    NEED_CURRENT_EVIDENCE,
                    True,
                    "continue_current_explanation",
                ),
            )
        elif intent.intent == INTENT_NEW_SUBJECT:
            specs = (
                (
                    NEED_SUBJECT_DISCOVERY,
                    True,
                    "resolve_new_subject_evidence_scope",
                ),
            )
        elif intent.intent == INTENT_UNRESOLVED:
            specs = ()

        requirements = []

        for index, (
            need_type,
            required,
            reason,
        ) in enumerate(specs, start=1):
            body = {
                "session_id": intent.session_id,
                "intent": intent.intent,
                "subject_hint": (
                    intent.resolved_subject_hint
                ),
                "need_type": need_type,
                "required": required,
                "reason": reason,
                "ordinal": index,
            }

            requirement_hash = deterministic_sha256(body)

            requirements.append(
                FollowUpEvidenceRequirement(
                    requirement_id=(
                        f"req.{requirement_hash[:24]}"
                    ),
                    subject_hint=(
                        intent.resolved_subject_hint
                    ),
                    need_type=need_type,
                    required=required,
                    reason=reason,
                    requirement_hash=requirement_hash,
                )
            )

        requirements = tuple(requirements)

        status = (
            "projected"
            if requirements
            else "unresolved"
        )

        body = {
            "session_id": intent.session_id,
            "intent": intent.intent,
            "subject_hint": intent.resolved_subject_hint,
            "requirement_hashes": tuple(
                item.requirement_hash
                for item in requirements
            ),
            "projection_status": status,
            "read_only": True,
        }

        return FollowUpEvidenceRequirementProjection(
            session_id=intent.session_id,
            intent=intent.intent,
            subject_hint=intent.resolved_subject_hint,
            requirements=requirements,
            projection_status=status,
            projection_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_followup_evidence_requirement_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-064 must remain read-only"
        )

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
        )
    ):
        raise AssertionError(
            "OI-064 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_064_REVISION",
    "NEED_CURRENT_EVIDENCE",
    "NEED_ADDITIONAL_EVIDENCE",
    "NEED_CONTRADICTORY_EVIDENCE",
    "NEED_TEMPORAL_EVIDENCE",
    "NEED_SUBJECT_DISCOVERY",
    "FollowUpEvidenceRequirement",
    "FollowUpEvidenceRequirementProjection",
    "FollowUpEvidenceRequirementProjector",
    "verify_followup_evidence_requirement_projection",
]
