from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
)
from qseries_v2.observation_intelligence.oi_049_explanation_evidence_ordering import (
    ExplanationEvidenceOrdering,
)
from qseries_v2.observation_intelligence.oi_050_explanation_completeness_evaluation import (
    OI_050_REVISION,
    COMPLETE,
    PARTIAL,
    INSUFFICIENT,
    ExplanationCompletenessEvaluator,
    verify_explanation_completeness_evaluation,
)


def resolution(
    supported=1,
    partial=0,
    unsupported=0,
):
    return ExplanationCandidateResolution(
        query_id="query.test",
        read_model_hash="a" * 64,
        items=(),
        supported_count=supported,
        partial_count=partial,
        unsupported_count=unsupported,
        resolution_hash="b" * 64,
        read_only=True,
    )


def ordering(count=1):
    return ExplanationEvidenceOrdering(
        query_id="query.test",
        items=(),
        item_count=count,
        ordering_hash="c" * 64,
        read_only=True,
    )


class TestOI050(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_completeness_evaluation()
        )

    def test_complete(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(),
            ordering=ordering(),
        )
        self.assertEqual(value.status, COMPLETE)

    def test_partial(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(supported=0, partial=1),
            ordering=ordering(),
        )
        self.assertEqual(value.status, PARTIAL)

    def test_insufficient(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(supported=0, unsupported=1),
            ordering=ordering(),
        )
        self.assertEqual(value.status, INSUFFICIENT)

    def test_empty(self):
        value = ExplanationCompletenessEvaluator().evaluate(
            resolution=resolution(supported=0),
            ordering=ordering(0),
        )
        self.assertEqual(value.status, INSUFFICIENT)
        self.assertIn(
            "no_ordered_explanation_evidence",
            value.reason_codes,
        )

    def test_deterministic(self):
        evaluator = ExplanationCompletenessEvaluator()

        a = evaluator.evaluate(
            resolution=resolution(),
            ordering=ordering(),
        )
        b = evaluator.evaluate(
            resolution=resolution(),
            ordering=ordering(),
        )

        self.assertEqual(
            a.evaluation_hash,
            b.evaluation_hash,
        )

    def test_side_effects(self):
        item = ExplanationCompletenessEvaluator()

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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-050 CERTIFICATION TEST")
    print(" EXPLANATION COMPLETENESS EVALUATION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI050)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-050")
    print(f"[PASS] Revision: {OI_050_REVISION}")
    print("[PASS] Complete, partial, and insufficient explanation states certified")
    print("[PASS] Missing or unsupported explanation evidence remains explicit")
    print("[PASS] Completeness evaluation is descriptive only and introduces no probability or score")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-050 CERTIFIED")
