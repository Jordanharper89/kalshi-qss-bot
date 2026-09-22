from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_045_oracle_reasoning_read_model import (
    OracleReasoningReadItem,
    OracleReasoningReadModel,
)
from qseries_v2.observation_intelligence.oi_046_explanation_candidate_resolution import (
    OI_046_REVISION,
    STATUS_PARTIAL,
    STATUS_SUPPORTED,
    ExplanationCandidateResolver,
    verify_explanation_candidate_resolution,
)

NOW = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)


def model(admission_status="admitted", missing=0):
    return OracleReasoningReadModel(
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status=admission_status,
        evidence_count=2,
        relationship_count=1,
        missing_need_count=missing,
        items=(
            OracleReasoningReadItem(
                subject="Astros strikeouts",
                signal_type="multi_evidence_context",
                support_class="multi_evidence_structure",
                evidence_count=2,
                context_roles=(
                    "evidence",
                    "market_state",
                    "sports_context",
                ),
                relationship_types=(
                    "same_subject",
                ),
                item_hash="a" * 64,
            ),
        ),
        built_at=NOW,
        read_model_hash="b" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI046(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_candidate_resolution()
        )

    def test_supported(self):
        result = ExplanationCandidateResolver().resolve(
            model()
        )

        self.assertEqual(
            result.items[0].status,
            STATUS_SUPPORTED,
        )

    def test_partial(self):
        result = ExplanationCandidateResolver().resolve(
            model("partial", 1)
        )

        self.assertEqual(
            result.items[0].status,
            STATUS_PARTIAL,
        )

    def test_reason_codes(self):
        result = ExplanationCandidateResolver().resolve(
            model("partial", 1)
        )

        self.assertIn(
            "missing_required_evidence",
            result.items[0].reason_codes,
        )

    def test_deterministic(self):
        resolver = ExplanationCandidateResolver()

        a = resolver.resolve(model())
        b = resolver.resolve(model())

        self.assertEqual(
            a.resolution_hash,
            b.resolution_hash,
        )

    def test_side_effects(self):
        resolver = ExplanationCandidateResolver()

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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-046 CERTIFICATION TEST")
    print(" EXPLANATION CANDIDATE RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI046
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-046")
    print(f"[PASS] Revision: {OI_046_REVISION}")
    print("[PASS] Supported, partial, and unsupported explanation candidates certified")
    print("[PASS] Missing evidence remains explicit in explanation readiness")
    print("[PASS] No causal claim, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-046 CERTIFIED")
