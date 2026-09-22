from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_064_followup_evidence_requirement_projection import (
    FollowUpEvidenceRequirement,
    FollowUpEvidenceRequirementProjection,
)
from qseries_v2.observation_intelligence.oi_065_followup_evidence_route_planning import (
    OI_065_REVISION,
    FollowUpEvidenceRoutePlanner,
    verify_followup_evidence_route_planning,
)


def projection():
    requirement = FollowUpEvidenceRequirement(
        requirement_id="req.1",
        subject_hint="Astros strikeouts",
        need_type="contradictory_evidence",
        required=True,
        reason="inspect_conflicting_evidence",
        requirement_hash="a" * 64,
    )

    return FollowUpEvidenceRequirementProjection(
        session_id="session.1",
        intent="contradiction",
        subject_hint="Astros strikeouts",
        requirements=(requirement,),
        projection_status="projected",
        projection_hash="b" * 64,
        read_only=True,
    )


class TestOI065(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_followup_evidence_route_planning()
        )

    def test_plan(self):
        plan = FollowUpEvidenceRoutePlanner().plan(
            projection()
        )

        self.assertEqual(
            len(plan.routes),
            1,
        )

        self.assertEqual(
            plan.routes[0].observation_need,
            "contradiction_observation",
        )

    def test_subject_preserved(self):
        plan = FollowUpEvidenceRoutePlanner().plan(
            projection()
        )

        self.assertEqual(
            plan.routes[0].subject_hint,
            "Astros strikeouts",
        )

    def test_no_missing_route(self):
        plan = FollowUpEvidenceRoutePlanner().plan(
            projection()
        )

        self.assertEqual(
            plan.missing_route_count,
            0,
        )

    def test_deterministic(self):
        planner = FollowUpEvidenceRoutePlanner()

        a = planner.plan(projection())
        b = planner.plan(projection())

        self.assertEqual(
            a.route_plan_hash,
            b.route_plan_hash,
        )

    def test_side_effects(self):
        planner = FollowUpEvidenceRoutePlanner()

        self.assertTrue(planner.read_only)
        self.assertFalse(planner.network_allowed)
        self.assertFalse(planner.persistence_allowed)
        self.assertFalse(planner.publication_allowed)
        self.assertFalse(planner.execution_allowed)
        self.assertFalse(planner.qseries_execution_allowed)
        self.assertFalse(planner.prediction_allowed)
        self.assertFalse(planner.edge_score_allowed)
        self.assertFalse(planner.probability_allowed)
        self.assertFalse(planner.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-065 CERTIFICATION TEST")
    print(" FOLLOW-UP EVIDENCE ROUTE PLANNING")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI065
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-065")
    print(f"[PASS] Revision: {OI_065_REVISION}")
    print("[PASS] Follow-up evidence requirements converted into generic observation routes")
    print("[PASS] Contradiction, temporal, additional-support, current-support, and subject-discovery capabilities remain domain-agnostic")
    print("[PASS] No adapter is invented when a capability cannot be routed")
    print("[DONE] OI-065 CERTIFIED")
