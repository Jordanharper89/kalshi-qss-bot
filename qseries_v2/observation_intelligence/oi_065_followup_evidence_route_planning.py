from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_064_followup_evidence_requirement_projection import (
    FollowUpEvidenceRequirementProjection,
    NEED_CURRENT_EVIDENCE,
    NEED_ADDITIONAL_EVIDENCE,
    NEED_CONTRADICTORY_EVIDENCE,
    NEED_TEMPORAL_EVIDENCE,
    NEED_SUBJECT_DISCOVERY,
)

BUILD_ID = "OI-065"
OI_065_REVISION = "OI_065_FOLLOWUP_EVIDENCE_ROUTE_PLANNING_V1"

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
class FollowUpEvidenceRoute:
    route_id: str
    requirement_id: str
    subject_hint: str | None
    observation_need: str
    capability_group: str
    required: bool
    route_hash: str


@dataclass(frozen=True, slots=True)
class FollowUpEvidenceRoutePlan:
    session_id: str
    subject_hint: str | None
    routes: tuple[FollowUpEvidenceRoute, ...]
    missing_route_count: int
    route_plan_hash: str
    read_only: bool


class FollowUpEvidenceRoutePlanner:
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

    _CAPABILITY_MAP = {
        NEED_CURRENT_EVIDENCE: (
            "subject_observation",
            "general_observation",
        ),
        NEED_ADDITIONAL_EVIDENCE: (
            "independent_support_observation",
            "general_observation",
        ),
        NEED_CONTRADICTORY_EVIDENCE: (
            "contradiction_observation",
            "general_observation",
        ),
        NEED_TEMPORAL_EVIDENCE: (
            "temporal_observation",
            "historical_observation",
        ),
        NEED_SUBJECT_DISCOVERY: (
            "subject_discovery",
            "discovery_observation",
        ),
    }

    def plan(
        self,
        projection: FollowUpEvidenceRequirementProjection,
    ) -> FollowUpEvidenceRoutePlan:
        if not isinstance(
            projection,
            FollowUpEvidenceRequirementProjection,
        ):
            raise TypeError(
                "projection must be "
                "FollowUpEvidenceRequirementProjection"
            )

        routes = []
        missing = 0

        for requirement in projection.requirements:
            mapped = self._CAPABILITY_MAP.get(
                requirement.need_type
            )

            if mapped is None:
                missing += 1
                continue

            observation_need, capability_group = mapped

            body = {
                "requirement_id": (
                    requirement.requirement_id
                ),
                "subject_hint": (
                    requirement.subject_hint
                ),
                "observation_need": observation_need,
                "capability_group": capability_group,
                "required": requirement.required,
            }

            route_hash = deterministic_sha256(body)

            routes.append(
                FollowUpEvidenceRoute(
                    route_id=(
                        f"route.{route_hash[:24]}"
                    ),
                    requirement_id=(
                        requirement.requirement_id
                    ),
                    subject_hint=(
                        requirement.subject_hint
                    ),
                    observation_need=observation_need,
                    capability_group=capability_group,
                    required=requirement.required,
                    route_hash=route_hash,
                )
            )

        routes = tuple(routes)

        body = {
            "session_id": projection.session_id,
            "subject_hint": projection.subject_hint,
            "route_hashes": tuple(
                item.route_hash
                for item in routes
            ),
            "missing_route_count": missing,
            "read_only": True,
        }

        return FollowUpEvidenceRoutePlan(
            session_id=projection.session_id,
            subject_hint=projection.subject_hint,
            routes=routes,
            missing_route_count=missing,
            route_plan_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_followup_evidence_route_planning() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-065 must remain read-only"
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
            "OI-065 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_065_REVISION",
    "FollowUpEvidenceRoute",
    "FollowUpEvidenceRoutePlan",
    "FollowUpEvidenceRoutePlanner",
    "verify_followup_evidence_route_planning",
]
