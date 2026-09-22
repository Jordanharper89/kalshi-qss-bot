from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_062_multi_subject_conversation_coordinator import (
    MultiSubjectConversationState,
)
from qseries_v2.observation_intelligence.oi_063_explanation_context_switch_resolution import (
    OI_063_REVISION,
    SWITCH_CURRENT,
    SWITCH_RESOLVED,
    SWITCH_UNRESOLVED,
    ExplanationContextSwitchResolver,
    verify_explanation_context_switch_resolution,
)


def state():
    return MultiSubjectConversationState(
        session_id="session.1",
        active_subject_hint="Bitcoin",
        subject_hints=(
            "Astros strikeouts",
            "Bitcoin",
        ),
        subject_turn_counts=(
            ("Astros strikeouts", 1),
            ("Bitcoin", 2),
        ),
        state_hash="a" * 64,
        read_only=True,
    )


class TestOI063(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_context_switch_resolution()
        )

    def test_resolved_switch(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="Astros strikeouts",
        )

        self.assertEqual(
            result.switch_status,
            SWITCH_RESOLVED,
        )

        self.assertEqual(
            result.resolved_subject_hint,
            "Astros strikeouts",
        )

    def test_current_switch(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="Bitcoin",
        )

        self.assertEqual(
            result.switch_status,
            SWITCH_CURRENT,
        )

    def test_unresolved_switch(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="Oil",
        )

        self.assertEqual(
            result.switch_status,
            SWITCH_UNRESOLVED,
        )

        self.assertIsNone(
            result.resolved_subject_hint
        )

    def test_case_insensitive(self):
        result = ExplanationContextSwitchResolver().resolve(
            state=state(),
            requested_subject_hint="bitcoin",
        )

        self.assertEqual(
            result.resolved_subject_hint,
            "Bitcoin",
        )

    def test_deterministic(self):
        resolver = ExplanationContextSwitchResolver()

        a = resolver.resolve(
            state=state(),
            requested_subject_hint="Astros strikeouts",
        )
        b = resolver.resolve(
            state=state(),
            requested_subject_hint="Astros strikeouts",
        )

        self.assertEqual(
            a.switch_hash,
            b.switch_hash,
        )

    def test_side_effects(self):
        resolver = ExplanationContextSwitchResolver()

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
    print(" OI-063 CERTIFICATION TEST")
    print(" EXPLANATION CONTEXT SWITCH RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI063)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-063")
    print(f"[PASS] Revision: {OI_063_REVISION}")
    print("[PASS] Resolved, current, and unresolved subject switches certified")
    print("[PASS] Known subject identity is preserved across deterministic context switches")
    print("[PASS] Unknown subjects fail closed without silently replacing active context")
    print("[DONE] OI-063 CERTIFIED")
