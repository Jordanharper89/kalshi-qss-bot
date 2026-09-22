from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OI_025_REVISION,
    QUERY_KIND_EVIDENCE,
    QUERY_KIND_EXPLANATION,
    QUERY_KIND_TIMELINE,
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
    verify_oracle_explanation_query_engine,
)


class TestOI025(unittest.TestCase):
    def setUp(self):
        self.engine = OracleExplanationQueryEngine(
            default_explanation_profile_map()
        )

    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_query_engine()
        )

    def test_explanation_query(self):
        query = self.engine.resolve(
            query_id="query.astros",
            text="Explain why the Astros strikeout edge moved",
            subject_hint="Astros strikeouts",
            domain="sports",
        )

        self.assertEqual(
            query.query_kind,
            QUERY_KIND_EXPLANATION,
        )

    def test_evidence_query(self):
        query = self.engine.resolve(
            query_id="query.btc",
            text="What evidence supports the Bitcoin move?",
            subject_hint="Bitcoin",
            domain="crypto",
        )

        self.assertEqual(
            query.query_kind,
            QUERY_KIND_EVIDENCE,
        )

    def test_timeline_query(self):
        query = self.engine.resolve(
            query_id="query.weather",
            text="Show the timeline for this hurricane market move",
            subject_hint="Hurricane market",
            domain="weather",
        )

        self.assertEqual(
            query.query_kind,
            QUERY_KIND_TIMELINE,
        )

    def test_generic_profile_fallback(self):
        query = self.engine.resolve(
            query_id="query.future",
            text="Why did this market move?",
            subject_hint="Future market",
            domain="future_domain",
        )

        self.assertEqual(
            query.profile_id,
            "profile.market_explanation",
        )

    def test_deterministic(self):
        a = self.engine.resolve(
            query_id="query.test",
            text="Why did this move?",
            subject_hint="Test",
            domain="sports",
        )
        b = self.engine.resolve(
            query_id="query.test",
            text="Why did this move?",
            subject_hint="Test",
            domain="sports",
        )

        self.assertEqual(
            a.query_hash,
            b.query_hash,
        )

    def test_side_effects(self):
        self.assertTrue(self.engine.read_only)
        self.assertFalse(self.engine.network_allowed)
        self.assertFalse(self.engine.persistence_allowed)
        self.assertFalse(self.engine.publication_allowed)
        self.assertFalse(self.engine.execution_allowed)
        self.assertFalse(self.engine.qseries_execution_allowed)
        self.assertFalse(self.engine.causal_claim_allowed)
        self.assertFalse(self.engine.prediction_allowed)
        self.assertFalse(self.engine.edge_score_allowed)
        self.assertFalse(self.engine.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-025 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION QUERY ENGINE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI025
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-025")
    print(f"[PASS] Revision: {OI_025_REVISION}")
    print("[PASS] Generic explanation, evidence, and timeline query classification certified")
    print("[PASS] Domain-to-explanation profile resolution and wildcard fallback certified")
    print("[PASS] Query engine remains universal across current and future adapter domains")
    print("[PASS] Causal claims, prediction, edge scoring, and execution remain disabled")
    print("[DONE] OI-025 CERTIFIED")
