from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_051_oracle_explanation_delivery_model import (
    OracleExplanationDeliveryModel,
)
from qseries_v2.observation_intelligence.oi_052_terminal_explanation_adapter import (
    OI_052_REVISION,
    TerminalExplanationAdapter,
    verify_terminal_explanation_adapter,
)

NOW = datetime(2026, 8, 11, 13, 0, tzinfo=timezone.utc)


def delivery():
    return OracleExplanationDeliveryModel(
        query_id="query.astros",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        headline="Oracle Evidence Explanation — Astros strikeouts",
        ordered_explanations=(
            "Astros strikeouts: two evidence items provide structural support.",
        ),
        caveats=(
            "partial_explanation_candidates",
            "structural association does not establish causation",
        ),
        delivered_at=NOW,
        delivery_hash="a" * 64,
        read_only=True,
        terminal_mutation_allowed=False,
    )


class TestOI052(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_explanation_adapter()
        )

    def test_adapt(self):
        view = TerminalExplanationAdapter().adapt(
            delivery()
        )

        self.assertEqual(
            view.completeness_status,
            "partial",
        )
        self.assertEqual(
            len(view.body_lines),
            1,
        )

    def test_footer(self):
        view = TerminalExplanationAdapter().adapt(
            delivery()
        )

        self.assertIn(
            "READ-ONLY",
            view.footer,
        )
        self.assertIn(
            "NO TRADE AUTHORIZATION",
            view.footer,
        )

    def test_deterministic(self):
        adapter = TerminalExplanationAdapter()

        a = adapter.adapt(delivery())
        b = adapter.adapt(delivery())

        self.assertEqual(
            a.view_hash,
            b.view_hash,
        )

    def test_side_effects(self):
        adapter = TerminalExplanationAdapter()

        self.assertTrue(adapter.read_only)
        self.assertFalse(adapter.network_allowed)
        self.assertFalse(adapter.persistence_allowed)
        self.assertFalse(adapter.publication_allowed)
        self.assertFalse(adapter.execution_allowed)
        self.assertFalse(adapter.qseries_execution_allowed)
        self.assertFalse(adapter.prediction_allowed)
        self.assertFalse(adapter.edge_score_allowed)
        self.assertFalse(adapter.probability_allowed)
        self.assertFalse(adapter.causal_claim_allowed)
        self.assertFalse(adapter.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-052 CERTIFICATION TEST")
    print(" TERMINAL EXPLANATION ADAPTER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI052)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-052")
    print(f"[PASS] Revision: {OI_052_REVISION}")
    print("[PASS] Oracle explanation delivery converted into deterministic terminal-safe view")
    print("[PASS] Completeness, explanation lines, caveats, subject, and read-only footer preserved")
    print("[PASS] Terminal mutation, prediction, probability, scoring, causation, and execution remain disabled")
    print("[DONE] OI-052 CERTIFIED")
