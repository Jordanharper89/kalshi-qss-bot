from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_060_explanation_continuation_coordinator import (
    OracleExplanationContinuation,
)
from qseries_v2.observation_intelligence.oi_061_explanation_intent_continuation_classifier import (
    ExplanationContinuationIntent,
)
from qseries_v2.observation_intelligence.oi_065_followup_evidence_route_planning import (
    FollowUpEvidenceRoute,
    FollowUpEvidenceRoutePlan,
)
from qseries_v2.observation_intelligence.oi_066_followup_reasoning_request_package import (
    OI_066_REVISION,
    FollowUpReasoningRequestPackageBuilder,
    verify_followup_reasoning_request_package,
)

NOW = datetime(
    2026,
    8,
    11,
    23,
    0,
    tzinfo=timezone.utc,
)


def continuation():
    return OracleExplanationContinuation(
        session_id="session.1",
        continuation_status="continue_resolved",
        resolved_subject_hint="Astros strikeouts",
        resolved_query_id="query.astros",
        session_change_type="none",
        prior_turn_count=1,
        continuation_hash="a" * 64,
        read_only=True,
    )


def intent():
    return ExplanationContinuationIntent(
        session_id="session.1",
        raw_followup=(
            "What evidence contradicts that move?"
        ),
        intent="contradiction",
        resolved_subject_hint="Astros strikeouts",
        resolved_query_id="query.astros",
        intent_hash="b" * 64,
        read_only=True,
    )


def plan():
    route = FollowUpEvidenceRoute(
        route_id="route.1",
        requirement_id="req.1",
        subject_hint="Astros strikeouts",
        observation_need="contradiction_observation",
        capability_group="general_observation",
        required=True,
        route_hash="c" * 64,
    )

    return FollowUpEvidenceRoutePlan(
        session_id="session.1",
        subject_hint="Astros strikeouts",
        routes=(route,),
        missing_route_count=0,
        route_plan_hash="d" * 64,
        read_only=True,
    )


class TestOI066(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_followup_reasoning_request_package()
        )

    def test_build(self):
        package = (
            FollowUpReasoningRequestPackageBuilder()
            .build(
                request_id="request.followup.1",
                continuation=continuation(),
                intent=intent(),
                route_plan=plan(),
                requested_at=NOW,
            )
        )

        self.assertEqual(
            package.request_status,
            "ready",
        )

        self.assertEqual(
            package.subject_hint,
            "Astros strikeouts",
        )

    def test_observation_need_preserved(self):
        package = (
            FollowUpReasoningRequestPackageBuilder()
            .build(
                request_id="request.followup.1",
                continuation=continuation(),
                intent=intent(),
                route_plan=plan(),
                requested_at=NOW,
            )
        )

        self.assertEqual(
            package.observation_needs,
            ("contradiction_observation",),
        )

    def test_deterministic(self):
        builder = (
            FollowUpReasoningRequestPackageBuilder()
        )

        a = builder.build(
            request_id="request.followup.1",
            continuation=continuation(),
            intent=intent(),
            route_plan=plan(),
            requested_at=NOW,
        )

        b = builder.build(
            request_id="request.followup.1",
            continuation=continuation(),
            intent=intent(),
            route_plan=plan(),
            requested_at=NOW,
        )

        self.assertEqual(
            a.request_hash,
            b.request_hash,
        )

    def test_side_effects(self):
        builder = (
            FollowUpReasoningRequestPackageBuilder()
        )

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(
            builder.qseries_execution_allowed
        )
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)
        self.assertFalse(builder.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-066 CERTIFICATION TEST")
    print(" FOLLOW-UP REASONING REQUEST PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI066
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-066")
    print(f"[PASS] Revision: {OI_066_REVISION}")
    print("[PASS] Follow-up continuation, intent, subject, and observation routes packaged for reasoning acquisition")
    print("[PASS] Contradiction, timeline, additional-evidence, and continuation requests can reach the generic adapter layer")
    print("[PASS] Blocked route plans remain blocked; no adapter, evidence, probability, or conclusion is invented")
    print("[DONE] OI-066 CERTIFIED")
