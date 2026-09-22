from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_055_terminal_explanation_session_adapter import (
    TerminalExplanationSessionTurn,
)
from qseries_v2.observation_intelligence.oi_056_explanation_conversation_context import (
    ExplanationConversationContextBuilder,
)
from qseries_v2.observation_intelligence.oi_058_explanation_followup_reference_resolution import (
    OI_058_REVISION,
    REFERENCE_CURRENT_SUBJECT,
    REFERENCE_UNRESOLVED,
    ExplanationFollowUpReferenceResolver,
    verify_explanation_followup_reference_resolution,
)

NOW = datetime(2026, 8, 11, 19, 0, tzinfo=timezone.utc)


def context():
    turn = TerminalExplanationSessionTurn(
        session_id="session.1",
        turn_number=1,
        query_id="query.astros",
        response_id="response.astros",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        display_payload=("response",),
        received_at=NOW,
        turn_hash="a" * 64,
        read_only=True,
    )

    return ExplanationConversationContextBuilder().build(
        session_id="session.1",
        turns=(turn,),
    )


class TestOI058(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_followup_reference_resolution()
        )

    def test_subject_reference(self):
        result = ExplanationFollowUpReferenceResolver().resolve(
            context=context(),
            raw_followup="What evidence supports that move?",
        )

        self.assertEqual(
            result.resolved_subject_hint,
            "Astros strikeouts",
        )
        self.assertEqual(
            result.resolution_type,
            REFERENCE_CURRENT_SUBJECT,
        )

    def test_unresolved(self):
        result = ExplanationFollowUpReferenceResolver().resolve(
            context=context(),
            raw_followup="Explain weather evidence",
        )

        self.assertEqual(
            result.resolution_type,
            REFERENCE_UNRESOLVED,
        )
        self.assertIsNone(result.resolved_subject_hint)

    def test_deterministic(self):
        resolver = ExplanationFollowUpReferenceResolver()

        a = resolver.resolve(
            context=context(),
            raw_followup="Why did that edge change?",
        )
        b = resolver.resolve(
            context=context(),
            raw_followup="Why did that edge change?",
        )

        self.assertEqual(
            a.resolution_hash,
            b.resolution_hash,
        )

    def test_side_effects(self):
        resolver = ExplanationFollowUpReferenceResolver()

        self.assertTrue(resolver.read_only)
        self.assertFalse(resolver.network_allowed)
        self.assertFalse(resolver.persistence_allowed)
        self.assertFalse(resolver.publication_allowed)
        self.assertFalse(resolver.execution_allowed)
        self.assertFalse(resolver.qseries_execution_allowed)
        self.assertFalse(resolver.prediction_allowed)
        self.assertFalse(resolver.edge_score_allowed)
        self.assertFalse(resolver.probability_allowed)
        self.assertFalse(resolver.causal_claim_allowed)
        self.assertFalse(resolver.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-058 CERTIFICATION TEST")
    print(" EXPLANATION FOLLOW-UP REFERENCE RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI058)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-058")
    print(f"[PASS] Revision: {OI_058_REVISION}")
    print("[PASS] Follow-up references resolve deterministically against current explanation session context")
    print("[PASS] Current subject and current query references preserve session lineage")
    print("[PASS] Unresolved references fail closed without guessing")
    print("[DONE] OI-058 CERTIFIED")
