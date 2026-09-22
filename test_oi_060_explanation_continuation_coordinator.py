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
    ExplanationFollowUpReferenceResolver,
)
from qseries_v2.observation_intelligence.oi_059_explanation_session_delta_projection import (
    ExplanationSessionDeltaProjector,
)
from qseries_v2.observation_intelligence.oi_060_explanation_continuation_coordinator import (
    OI_060_REVISION,
    CONTINUE_RESOLVED,
    CONTINUE_UNRESOLVED,
    OracleExplanationContinuationCoordinator,
    verify_explanation_continuation_coordinator,
)

NOW = datetime(2026, 8, 11, 21, 0, tzinfo=timezone.utc)


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


class TestOI060(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_continuation_coordinator()
        )

    def test_resolved_continuation(self):
        ctx = context()
        reference = ExplanationFollowUpReferenceResolver().resolve(
            context=ctx,
            raw_followup="What evidence supports that move?",
        )
        delta = ExplanationSessionDeltaProjector().project(ctx)

        result = OracleExplanationContinuationCoordinator().coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )

        self.assertEqual(
            result.continuation_status,
            CONTINUE_RESOLVED,
        )
        self.assertEqual(
            result.resolved_subject_hint,
            "Astros strikeouts",
        )

    def test_unresolved_continuation(self):
        ctx = context()
        reference = ExplanationFollowUpReferenceResolver().resolve(
            context=ctx,
            raw_followup="Explain weather evidence",
        )
        delta = ExplanationSessionDeltaProjector().project(ctx)

        result = OracleExplanationContinuationCoordinator().coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )

        self.assertEqual(
            result.continuation_status,
            CONTINUE_UNRESOLVED,
        )

    def test_deterministic(self):
        ctx = context()
        reference = ExplanationFollowUpReferenceResolver().resolve(
            context=ctx,
            raw_followup="Why did that edge change?",
        )
        delta = ExplanationSessionDeltaProjector().project(ctx)

        coordinator = OracleExplanationContinuationCoordinator()

        a = coordinator.coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )
        b = coordinator.coordinate(
            context=ctx,
            reference=reference,
            delta=delta,
        )

        self.assertEqual(
            a.continuation_hash,
            b.continuation_hash,
        )

    def test_side_effects(self):
        coordinator = OracleExplanationContinuationCoordinator()

        self.assertTrue(coordinator.read_only)
        self.assertFalse(coordinator.network_allowed)
        self.assertFalse(coordinator.persistence_allowed)
        self.assertFalse(coordinator.publication_allowed)
        self.assertFalse(coordinator.execution_allowed)
        self.assertFalse(coordinator.qseries_execution_allowed)
        self.assertFalse(coordinator.prediction_allowed)
        self.assertFalse(coordinator.edge_score_allowed)
        self.assertFalse(coordinator.probability_allowed)
        self.assertFalse(coordinator.causal_claim_allowed)
        self.assertFalse(coordinator.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-060 CERTIFICATION TEST")
    print(" EXPLANATION CONTINUATION COORDINATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI060)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-060")
    print(f"[PASS] Revision: {OI_060_REVISION}")
    print("[PASS] Resolved and unresolved explanation continuations coordinated deterministically")
    print("[PASS] Session identity, reference lineage, prior turn count, and session change type preserved")
    print("[PASS] Unresolved follow-ups fail closed without guessing or silently changing subject")
    print("[DONE] OI-060 CERTIFIED")
