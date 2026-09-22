from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_024_oracle_explanation_read_model import (
    OracleExplanationReadModel,
    OracleExplanationTimelineEntry,
)
from qseries_v2.observation_intelligence.oi_025_oracle_explanation_query_engine import (
    OracleExplanationQueryEngine,
    default_explanation_profile_map,
)
from qseries_v2.observation_intelligence.oi_026_evidence_explanation_formatter import (
    OI_026_REVISION,
    EvidenceExplanationFormatter,
    verify_evidence_explanation_formatter,
)

NOW = datetime(2026, 8, 10, 18, 0, tzinfo=timezone.utc)


def query():
    return OracleExplanationQueryEngine(
        default_explanation_profile_map()
    ).resolve(
        query_id="query.astros",
        text="Explain why the Astros strikeout edge moved",
        subject_hint="Astros strikeouts",
        domain="sports",
    )


def model():
    return OracleExplanationReadModel(
        query_id="query.astros",
        profile_id="profile.market_explanation",
        built_at=NOW,
        sufficient_evidence=True,
        completeness_status="complete",
        evidence_item_count=3,
        distinct_source_count=2,
        stale_evidence_count=0,
        supporting_relationship_count=2,
        contradicting_relationship_count=1,
        timeline=(
            OracleExplanationTimelineEntry(
                ordinal=1,
                evidence_observation_id="obs.lineup",
                temporal_relation="before",
                seconds_from_change_observation=-120,
                agreement_count=1,
                contradiction_count=0,
            ),
        ),
        missing_required_evidence=False,
        read_model_hash="a" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
        probability_allowed=False,
        read_only=True,
    )


class TestOI026(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_explanation_formatter()
        )

    def test_format(self):
        view = EvidenceExplanationFormatter().format(
            query=query(),
            model=model(),
        )

        self.assertIn(
            "Astros strikeouts",
            view.title,
        )
        self.assertEqual(
            len(view.timeline_lines),
            1,
        )

    def test_contradiction_caveat(self):
        view = EvidenceExplanationFormatter().format(
            query=query(),
            model=model(),
        )

        self.assertTrue(
            any(
                "Contradicting evidence" in line
                for line in view.caveat_lines
            )
        )

    def test_non_causal(self):
        view = EvidenceExplanationFormatter().format(
            query=query(),
            model=model(),
        )

        self.assertFalse(view.predictive)
        self.assertFalse(view.causal_claim_allowed)
        self.assertTrue(view.read_only)

    def test_deterministic(self):
        formatter = EvidenceExplanationFormatter()

        a = formatter.format(
            query=query(),
            model=model(),
        )
        b = formatter.format(
            query=query(),
            model=model(),
        )

        self.assertEqual(a.view_hash, b.view_hash)

    def test_side_effects(self):
        formatter = EvidenceExplanationFormatter()

        self.assertTrue(formatter.read_only)
        self.assertFalse(formatter.network_allowed)
        self.assertFalse(formatter.persistence_allowed)
        self.assertFalse(formatter.publication_allowed)
        self.assertFalse(formatter.execution_allowed)
        self.assertFalse(formatter.qseries_execution_allowed)
        self.assertFalse(formatter.causal_claim_allowed)
        self.assertFalse(formatter.prediction_allowed)
        self.assertFalse(formatter.edge_score_allowed)
        self.assertFalse(formatter.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-026 CERTIFICATION TEST")
    print(" EVIDENCE EXPLANATION FORMATTER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI026
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-026")
    print(f"[PASS] Revision: {OI_026_REVISION}")
    print("[PASS] Explanation read models format into deterministic operator-readable evidence views")
    print("[PASS] Timeline, completeness, source diversity, contradictions, and caveats preserved")
    print("[PASS] Formatter remains non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-026 CERTIFIED")
