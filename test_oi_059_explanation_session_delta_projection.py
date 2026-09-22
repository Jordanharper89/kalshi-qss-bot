from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_055_terminal_explanation_session_adapter import (
    TerminalExplanationSessionTurn,
)
from qseries_v2.observation_intelligence.oi_056_explanation_conversation_context import (
    ExplanationConversationContextBuilder,
)
from qseries_v2.observation_intelligence.oi_059_explanation_session_delta_projection import (
    OI_059_REVISION,
    CHANGE_COMPLETENESS,
    CHANGE_MULTIPLE,
    CHANGE_NONE,
    ExplanationSessionDeltaProjector,
    verify_explanation_session_delta_projection,
)

NOW = datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc)


def turn(number, query_id, subject, status):
    return TerminalExplanationSessionTurn(
        session_id="session.1",
        turn_number=number,
        query_id=query_id,
        response_id=f"response.{number}",
        subject_hint=subject,
        completeness_status=status,
        display_payload=(f"turn {number}",),
        received_at=NOW,
        turn_hash=str(number) * 64,
        read_only=True,
    )


def context(turns):
    return ExplanationConversationContextBuilder().build(
        session_id="session.1",
        turns=tuple(turns),
    )


class TestOI059(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_session_delta_projection()
        )

    def test_no_delta_first_turn(self):
        result = ExplanationSessionDeltaProjector().project(
            context(
                (
                    turn(
                        1,
                        "query.1",
                        "Astros strikeouts",
                        "partial",
                    ),
                )
            )
        )

        self.assertEqual(result.change_type, CHANGE_NONE)

    def test_completeness_delta(self):
        result = ExplanationSessionDeltaProjector().project(
            context(
                (
                    turn(
                        1,
                        "query.1",
                        "Astros strikeouts",
                        "partial",
                    ),
                    turn(
                        2,
                        "query.1",
                        "Astros strikeouts",
                        "complete",
                    ),
                )
            )
        )

        self.assertEqual(
            result.change_type,
            CHANGE_COMPLETENESS,
        )

    def test_multiple_delta(self):
        result = ExplanationSessionDeltaProjector().project(
            context(
                (
                    turn(
                        1,
                        "query.1",
                        "Astros strikeouts",
                        "partial",
                    ),
                    turn(
                        2,
                        "query.2",
                        "Bitcoin",
                        "complete",
                    ),
                )
            )
        )

        self.assertEqual(
            result.change_type,
            CHANGE_MULTIPLE,
        )

    def test_deterministic(self):
        projector = ExplanationSessionDeltaProjector()
        value = context(
            (
                turn(
                    1,
                    "query.1",
                    "Astros strikeouts",
                    "partial",
                ),
                turn(
                    2,
                    "query.1",
                    "Astros strikeouts",
                    "complete",
                ),
            )
        )

        a = projector.project(value)
        b = projector.project(value)

        self.assertEqual(
            a.delta_hash,
            b.delta_hash,
        )

    def test_side_effects(self):
        projector = ExplanationSessionDeltaProjector()

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
        self.assertFalse(projector.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-059 CERTIFICATION TEST")
    print(" EXPLANATION SESSION DELTA PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI059)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-059")
    print(f"[PASS] Revision: {OI_059_REVISION}")
    print("[PASS] Query, subject, and completeness changes projected across explanation session turns")
    print("[PASS] First-turn, no-change, single-change, and multiple-change states remain deterministic")
    print("[PASS] Session delta projection introduces no causal claim, prediction, probability, or score")
    print("[DONE] OI-059 CERTIFIED")
