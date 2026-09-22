from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_060_explanation_continuation_coordinator import (
    OracleExplanationContinuation,
)
from .oi_061_explanation_intent_continuation_classifier import (
    ExplanationContinuationIntent,
)
from .oi_065_followup_evidence_route_planning import (
    FollowUpEvidenceRoutePlan,
)

BUILD_ID = "OI-066"
OI_066_REVISION = "OI_066_FOLLOWUP_REASONING_REQUEST_PACKAGE_V1"

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


@dataclass(frozen=True, slots=True)
class FollowUpReasoningRequestPackage:
    request_id: str
    session_id: str
    intent: str
    subject_hint: str | None
    prior_query_id: str | None
    route_ids: tuple[str, ...]
    observation_needs: tuple[str, ...]
    route_plan_hash: str
    requested_at: datetime
    request_status: str
    request_hash: str
    read_only: bool


class FollowUpReasoningRequestPackageBuilder:
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

    def build(
        self,
        *,
        request_id: str,
        continuation: OracleExplanationContinuation,
        intent: ExplanationContinuationIntent,
        route_plan: FollowUpEvidenceRoutePlan,
        requested_at: datetime,
    ) -> FollowUpReasoningRequestPackage:
        request_id_value = str(request_id).strip()

        if not request_id_value:
            raise ValueError(
                "request_id must not be empty"
            )

        if not isinstance(
            continuation,
            OracleExplanationContinuation,
        ):
            raise TypeError(
                "continuation must be "
                "OracleExplanationContinuation"
            )

        if not isinstance(
            intent,
            ExplanationContinuationIntent,
        ):
            raise TypeError(
                "intent must be "
                "ExplanationContinuationIntent"
            )

        if not isinstance(
            route_plan,
            FollowUpEvidenceRoutePlan,
        ):
            raise TypeError(
                "route_plan must be "
                "FollowUpEvidenceRoutePlan"
            )

        if not (
            continuation.session_id
            == intent.session_id
            == route_plan.session_id
        ):
            raise ValueError(
                "continuation/intent/route plan "
                "session_id mismatch"
            )

        if not isinstance(
            requested_at,
            datetime,
        ):
            raise TypeError(
                "requested_at must be datetime"
            )

        if requested_at.tzinfo is None:
            raise ValueError(
                "requested_at must be timezone-aware"
            )

        requested_at = requested_at.astimezone(
            timezone.utc
        )

        route_ids = tuple(
            item.route_id
            for item in route_plan.routes
        )

        observation_needs = tuple(
            item.observation_need
            for item in route_plan.routes
        )

        status = (
            "ready"
            if route_plan.routes
            and route_plan.missing_route_count == 0
            else "blocked"
        )

        body = {
            "request_id": request_id_value,
            "session_id": continuation.session_id,
            "intent": intent.intent,
            "subject_hint": (
                intent.resolved_subject_hint
            ),
            "prior_query_id": (
                intent.resolved_query_id
            ),
            "route_ids": route_ids,
            "observation_needs": observation_needs,
            "route_plan_hash": (
                route_plan.route_plan_hash
            ),
            "requested_at": requested_at,
            "request_status": status,
            "read_only": True,
        }

        return FollowUpReasoningRequestPackage(
            request_id=request_id_value,
            session_id=continuation.session_id,
            intent=intent.intent,
            subject_hint=(
                intent.resolved_subject_hint
            ),
            prior_query_id=(
                intent.resolved_query_id
            ),
            route_ids=route_ids,
            observation_needs=observation_needs,
            route_plan_hash=(
                route_plan.route_plan_hash
            ),
            requested_at=requested_at,
            request_status=status,
            request_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_followup_reasoning_request_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-066 must remain read-only"
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
            "OI-066 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_066_REVISION",
    "FollowUpReasoningRequestPackage",
    "FollowUpReasoningRequestPackageBuilder",
    "verify_followup_reasoning_request_package",
]
