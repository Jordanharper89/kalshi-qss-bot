from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_055_terminal_explanation_session_adapter import (
    TerminalExplanationSessionTurn,
)
from qseries_v2.observation_intelligence.oi_056_explanation_conversation_context import (
    ExplanationConversationContextBuilder,
)
from qseries_v2.observation_intelligence.oi_062_multi_subject_conversation_coordinator import (
    OI_062_REVISION,
    MultiSubjectConversationCoordinator,
    verify_multi_subject_conversation_coordinator,
)

NOW = datetime(2026, 8, 11, 22, 0, tzinfo=timezone.utc)


def turn(number, subject):
    return TerminalExplanationSessionTurn(
        session_id="session.1",
        turn_number=number,
        query_id=f"query.{number}",
        response_id=f"response.{number}",
        subject_hint=subject,
        completeness_status="complete",
        display_payload=(subject,),
        received_at=NOW,
        turn_hash=str(number) * 64,
        read_only=True,
    )


def context():
    return ExplanationConversationContextBuilder().build(
        session_id="session.1",
        turns=(
            turn(1, "Bitcoin"),
            turn(2, "Astros strikeouts"),
            turn(3, "Bitcoin"),
        ),
    )


class TestOI062(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_multi_subject_conversation_coordinator()
        )

    def test_subjects(self):
        state = MultiSubjectConversationCoordinator().coordinate(
            context()
        )

        self.assertEqual(
            state.subject_hints,
            (
                "Astros strikeouts",
                "Bitcoin",
            ),
        )

    def test_active_subject(self):
        state = MultiSubjectConversationCoordinator().coordinate(
            context()
        )

        self.assertEqual(
            state.active_subject_hint,
            "Bitcoin",
        )

    def test_turn_counts(self):
        state = MultiSubjectConversationCoordinator().coordinate(
            context()
        )

        self.assertIn(
            ("Bitcoin", 2),
            state.subject_turn_counts,
        )

        self.assertIn(
            ("Astros strikeouts", 1),
            state.subject_turn_counts,
        )

    def test_deterministic(self):
        coordinator = MultiSubjectConversationCoordinator()

        a = coordinator.coordinate(context())
        b = coordinator.coordinate(context())

        self.assertEqual(
            a.state_hash,
            b.state_hash,
        )

    def test_side_effects(self):
        item = MultiSubjectConversationCoordinator()

        self.assertTrue(item.read_only)
        self.assertFalse(item.network_allowed)
        self.assertFalse(item.persistence_allowed)
        self.assertFalse(item.publication_allowed)
        self.assertFalse(item.execution_allowed)
        self.assertFalse(item.qseries_execution_allowed)
        self.assertFalse(item.prediction_allowed)
        self.assertFalse(item.edge_score_allowed)
        self.assertFalse(item.probability_allowed)
        self.assertFalse(item.causal_claim_allowed)
        self.assertFalse(item.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-062 CERTIFICATION TEST")
    print(" MULTI-SUBJECT CONVERSATION COORDINATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI062)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-062")
    print(f"[PASS] Revision: {OI_062_REVISION}")
    print("[PASS] Multiple explanation subjects coordinated within one deterministic session")
    print("[PASS] Active subject, known subjects, and per-subject turn counts certified")
    print("[PASS] Multi-subject state remains read-only, non-mutating, and non-predictive")
    print("[DONE] OI-062 CERTIFIED")
