from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_062_multi_subject_conversation_coordinator import (
    MultiSubjectConversationState,
)

BUILD_ID = "OI-063"
OI_063_REVISION = "OI_063_EXPLANATION_CONTEXT_SWITCH_RESOLUTION_V1"

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

SWITCH_RESOLVED = "switch_resolved"
SWITCH_CURRENT = "switch_current"
SWITCH_UNRESOLVED = "switch_unresolved"


@dataclass(frozen=True, slots=True)
class ExplanationContextSwitchResolution:
    session_id: str
    requested_subject_hint: str
    prior_active_subject_hint: str | None
    resolved_subject_hint: str | None
    switch_status: str
    switch_hash: str
    read_only: bool


class ExplanationContextSwitchResolver:
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

    def resolve(
        self,
        *,
        state: MultiSubjectConversationState,
        requested_subject_hint: str,
    ) -> ExplanationContextSwitchResolution:
        if not isinstance(
            state,
            MultiSubjectConversationState,
        ):
            raise TypeError(
                "state must be MultiSubjectConversationState"
            )

        requested = " ".join(
            str(requested_subject_hint).strip().split()
        )

        if not requested:
            raise ValueError(
                "requested_subject_hint must not be empty"
            )

        normalized_map = {
            subject.lower(): subject
            for subject in state.subject_hints
        }

        resolved = normalized_map.get(
            requested.lower()
        )

        if resolved is None:
            status = SWITCH_UNRESOLVED
        elif resolved == state.active_subject_hint:
            status = SWITCH_CURRENT
        else:
            status = SWITCH_RESOLVED

        body = {
            "session_id": state.session_id,
            "requested_subject_hint": requested,
            "prior_active_subject_hint": (
                state.active_subject_hint
            ),
            "resolved_subject_hint": resolved,
            "switch_status": status,
            "read_only": True,
        }

        return ExplanationContextSwitchResolution(
            session_id=state.session_id,
            requested_subject_hint=requested,
            prior_active_subject_hint=(
                state.active_subject_hint
            ),
            resolved_subject_hint=resolved,
            switch_status=status,
            switch_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_context_switch_resolution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-063 must remain read-only")

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
            "OI-063 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_063_REVISION",
    "SWITCH_RESOLVED",
    "SWITCH_CURRENT",
    "SWITCH_UNRESOLVED",
    "ExplanationContextSwitchResolution",
    "ExplanationContextSwitchResolver",
    "verify_explanation_context_switch_resolution",
]
