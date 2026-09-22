from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_052_terminal_explanation_adapter import (
    TerminalExplanationView,
)
from qseries_v2.observation_intelligence.oi_053_explanation_query_response_package import (
    OI_053_REVISION,
    ExplanationQueryResponsePackageBuilder,
    verify_explanation_query_response_package,
)

NOW = datetime(2026, 8, 11, 14, 0, tzinfo=timezone.utc)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def view():
    return TerminalExplanationView(
        query_id="query.astros",
        subject_hint="Astros strikeouts",
        completeness_status="partial",
        title="Oracle Evidence Explanation — Astros strikeouts",
        body_lines=("Explanation line",),
        caveat_lines=("missing_required_evidence",),
        footer="MODE: READ-ONLY | NO TRADE AUTHORIZATION | NO CAUSAL CLAIM",
        view_hash="a" * 64,
        read_only=True,
    )


class TestOI053(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_query_response_package()
        )

    def test_build(self):
        package = ExplanationQueryResponsePackageBuilder().build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.query_id,
            "query.astros",
        )
        self.assertEqual(
            package.completeness_status,
            "partial",
        )

    def test_body_preserved(self):
        package = ExplanationQueryResponsePackageBuilder().build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        self.assertEqual(
            package.body_lines,
            ("Explanation line",),
        )

    def test_deterministic(self):
        builder = ExplanationQueryResponsePackageBuilder()

        a = builder.build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        b = builder.build(
            response_id="response.astros",
            query=query(),
            view=view(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.response_hash,
            b.response_hash,
        )

    def test_side_effects(self):
        builder = ExplanationQueryResponsePackageBuilder()

        self.assertTrue(builder.read_only)
        self.assertFalse(builder.network_allowed)
        self.assertFalse(builder.persistence_allowed)
        self.assertFalse(builder.publication_allowed)
        self.assertFalse(builder.execution_allowed)
        self.assertFalse(builder.qseries_execution_allowed)
        self.assertFalse(builder.prediction_allowed)
        self.assertFalse(builder.edge_score_allowed)
        self.assertFalse(builder.probability_allowed)
        self.assertFalse(builder.causal_claim_allowed)
        self.assertFalse(builder.terminal_mutation_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-053 CERTIFICATION TEST")
    print(" EXPLANATION QUERY RESPONSE PACKAGE")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI053)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-053")
    print(f"[PASS] Revision: {OI_053_REVISION}")
    print("[PASS] Explanation query identity and terminal-safe view packaged into deterministic response")
    print("[PASS] Subject, completeness, explanation body, caveats, and read-only footer preserved")
    print("[PASS] Publication, terminal mutation, prediction, probability, scoring, causation, and execution remain disabled")
    print("[DONE] OI-053 CERTIFIED")
