from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_061_explanation_intent_continuation_classifier import (
    ExplanationContinuationIntent,
    INTENT_MORE_EVIDENCE,
    INTENT_CONTRADICTION,
    INTENT_TIMELINE,
    INTENT_UNRESOLVED,
)
from qseries_v2.observation_intelligence.oi_064_followup_evidence_requirement_projection import (
    OI_064_REVISION,
    NEED_ADDITIONAL_EVIDENCE,
    NEED_CONTRADICTORY_EVIDENCE,
    NEED_TEMPORAL_EVIDENCE,
    FollowUpEvidenceRequirementProjector,
    verify_followup_evidence_requirement_projection,
)


def intent(kind):
    return ExplanationContinuationIntent(
        session_id="session.1",
        raw_followup="follow up",
        intent=kind,
        resolved_subject_hint="Astros strikeouts",
        resolved_query_id="query.astros",
        intent_hash="a" * 64,
        read_only=True,
    )


class TestOI064(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_followup_evidence_requirement_projection()
        )

    def test_more_evidence(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_MORE_EVIDENCE)
        )

        self.assertIn(
            NEED_ADDITIONAL_EVIDENCE,
            tuple(
                item.need_type
                for item in result.requirements
            ),
        )

    def test_contradiction(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_CONTRADICTION)
        )

        self.assertIn(
            NEED_CONTRADICTORY_EVIDENCE,
            tuple(
                item.need_type
                for item in result.requirements
            ),
        )

    def test_timeline(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_TIMELINE)
        )

        self.assertIn(
            NEED_TEMPORAL_EVIDENCE,
            tuple(
                item.need_type
                for item in result.requirements
            ),
        )

    def test_unresolved_fails_closed(self):
        result = FollowUpEvidenceRequirementProjector().project(
            intent(INTENT_UNRESOLVED)
        )

        self.assertEqual(
            result.requirements,
            (),
        )
        self.assertEqual(
            result.projection_status,
            "unresolved",
        )

    def test_deterministic(self):
        projector = FollowUpEvidenceRequirementProjector()

        a = projector.project(
            intent(INTENT_MORE_EVIDENCE)
        )
        b = projector.project(
            intent(INTENT_MORE_EVIDENCE)
        )

        self.assertEqual(
            a.projection_hash,
            b.projection_hash,
        )

    def test_side_effects(self):
        projector = FollowUpEvidenceRequirementProjector()

        self.assertTrue(projector.read_only)
        self.assertFalse(projector.network_allowed)
        self.assertFalse(projector.persistence_allowed)
        self.assertFalse(projector.publication_allowed)
        self.assertFalse(projector.execution_allowed)
        self.assertFalse(projector.qseries_execution_allowed)
        self.assertFalse(projector.prediction_allowed)
        self.assertFalse(projector.edge_score_allowed)
        self.assertFalse(projector.probability_allowed)
        self.assertFalse(projector.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-064 CERTIFICATION TEST")
    print(" FOLLOW-UP EVIDENCE REQUIREMENT PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI064
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-064")
    print(f"[PASS] Revision: {OI_064_REVISION}")
    print("[PASS] Follow-up intents project into explicit generic evidence requirements")
    print("[PASS] More-evidence, contradiction, timeline, continuation, and new-subject needs remain domain-agnostic")
    print("[PASS] Unresolved follow-ups fail closed without inventing evidence requirements")
    print("[DONE] OI-064 CERTIFIED")
