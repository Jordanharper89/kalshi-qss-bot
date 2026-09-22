from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_053_explanation_query_response_package import (
    ExplanationQueryResponsePackage,
)
from qseries_v2.observation_intelligence.oi_054_explanation_terminal_handoff_boundary import (
    OI_054_REVISION,
    ExplanationTerminalHandoffBoundary,
    verify_explanation_terminal_handoff_boundary,
)

NOW = datetime(2026, 8, 11, 15, 0, tzinfo=timezone.utc)


def package():
    return ExplanationQueryResponsePackage(
        response_id="response.astros",
        query_id="query.astros",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        title="Oracle Evidence Explanation — Astros strikeouts",
        body_lines=(
            "Astros strikeouts: evidence explanation line.",
        ),
        caveat_lines=(
            "missing_required_evidence",
            "structural association does not establish causation",
        ),
        footer=(
            "MODE: READ-ONLY | "
            "NO TRADE AUTHORIZATION | "
            "NO CAUSAL CLAIM"
        ),
        assembled_at=NOW,
        response_hash="a" * 64,
        read_only=True,
    )


class TestOI054(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_terminal_handoff_boundary()
        )

    def test_handoff(self):
        value = ExplanationTerminalHandoffBoundary().handoff(
            package()
        )

        self.assertEqual(
            value.completeness_status,
            "partial",
        )

        self.assertIn(
            "STATUS: PARTIAL",
            value.display_payload,
        )

    def test_caveats_rendered(self):
        value = ExplanationTerminalHandoffBoundary().handoff(
            package()
        )

        payload = "\n".join(
            value.display_payload
        )

        self.assertIn(
            "missing_required_evidence",
            payload,
        )

        self.assertIn(
            "NO TRADE AUTHORIZATION",
            payload,
        )

    def test_deterministic(self):
        boundary = ExplanationTerminalHandoffBoundary()

        a = boundary.handoff(package())
        b = boundary.handoff(package())

        self.assertEqual(
            a.handoff_hash,
            b.handoff_hash,
        )

    def test_side_effects(self):
        boundary = ExplanationTerminalHandoffBoundary()

        self.assertTrue(boundary.read_only)
        self.assertFalse(boundary.network_allowed)
        self.assertFalse(boundary.persistence_allowed)
        self.assertFalse(boundary.publication_allowed)
        self.assertFalse(boundary.execution_allowed)
        self.assertFalse(boundary.qseries_execution_allowed)
        self.assertFalse(boundary.prediction_allowed)
        self.assertFalse(boundary.edge_score_allowed)
        self.assertFalse(boundary.probability_allowed)
        self.assertFalse(boundary.causal_claim_allowed)
        self.assertFalse(boundary.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-054 CERTIFICATION TEST")
    print(" EXPLANATION TERMINAL HANDOFF BOUNDARY")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI054)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-054")
    print(f"[PASS] Revision: {OI_054_REVISION}")
    print("[PASS] Explanation response package converted into deterministic terminal handoff payload")
    print("[PASS] Status, explanation body, caveats, subject identity, and read-only safety footer preserved")
    print("[PASS] Handoff remains non-mutating and cannot publish, predict, score, authorize, or execute")
    print("[DONE] OI-054 CERTIFIED")
