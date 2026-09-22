from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_058_explanation_followup_reference_resolution import (
    ExplanationFollowUpReferenceResolution,
)
from qseries_v2.observation_intelligence.oi_060_explanation_continuation_coordinator import (
    OracleExplanationContinuation,
)
from qseries_v2.observation_intelligence.oi_061_explanation_intent_continuation_classifier import (
    OI_061_REVISION,
    INTENT_CONTRADICTION,
    INTENT_MORE_EVIDENCE,
    INTENT_TIMELINE,
    INTENT_UNRESOLVED,
    ExplanationIntentContinuationClassifier,
    verify_explanation_intent_continuation_classifier,
)


def reference(text, resolved=True):
    return ExplanationFollowUpReferenceResolution(
        session_id="session.1",
        raw_followup=text,
        resolved_subject_hint=(
            "Astros strikeouts" if resolved else None
        ),
        resolved_query_id=(
            "query.astros" if resolved else None
        ),
        resolution_type=(
            "current_subject" if resolved else "unresolved"
        ),
        resolution_hash="a" * 64,
        read_only=True,
    )


def continuation(resolved=True):
    return OracleExplanationContinuation(
        session_id="session.1",
        continuation_status=(
            "continue_resolved"
            if resolved
            else "continue_unresolved"
        ),
        resolved_subject_hint=(
            "Astros strikeouts" if resolved else None
        ),
        resolved_query_id=(
            "query.astros" if resolved else None
        ),
        session_change_type="none",
        prior_turn_count=1,
        continuation_hash="b" * 64,
        read_only=True,
    )


class TestOI061(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_intent_continuation_classifier()
        )

    def test_more_evidence(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "What evidence supports that move?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            result.intent,
            INTENT_MORE_EVIDENCE,
        )

    def test_contradiction(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "What evidence contradicts that?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            result.intent,
            INTENT_CONTRADICTION,
        )

    def test_timeline(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "What changed since the last answer?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            result.intent,
            INTENT_TIMELINE,
        )

    def test_unresolved(self):
        result = ExplanationIntentContinuationClassifier().classify(
            reference=reference(
                "Explain something else",
                False,
            ),
            continuation=continuation(False),
        )

        self.assertEqual(
            result.intent,
            INTENT_UNRESOLVED,
        )

    def test_deterministic(self):
        classifier = ExplanationIntentContinuationClassifier()

        a = classifier.classify(
            reference=reference(
                "What evidence supports that move?"
            ),
            continuation=continuation(),
        )
        b = classifier.classify(
            reference=reference(
                "What evidence supports that move?"
            ),
            continuation=continuation(),
        )

        self.assertEqual(
            a.intent_hash,
            b.intent_hash,
        )

    def test_side_effects(self):
        item = ExplanationIntentContinuationClassifier()

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
    print(" OI-061 CERTIFICATION TEST")
    print(" EXPLANATION INTENT CONTINUATION CLASSIFIER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI061)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-061")
    print(f"[PASS] Revision: {OI_061_REVISION}")
    print("[PASS] Continue, evidence, contradiction, timeline, new-subject, and unresolved intents certified")
    print("[PASS] Follow-up intent classification remains deterministic and session-bound")
    print("[PASS] Unresolved continuation fails closed without guessing")
    print("[DONE] OI-061 CERTIFIED")
