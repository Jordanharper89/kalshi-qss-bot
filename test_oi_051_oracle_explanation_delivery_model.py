from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_048_oracle_explanation_readout import (
    OracleExplanationReadout,
)
from qseries_v2.observation_intelligence.oi_049_explanation_evidence_ordering import (
    OrderedExplanationEvidenceItem,
    ExplanationEvidenceOrdering,
)
from qseries_v2.observation_intelligence.oi_050_explanation_completeness_evaluation import (
    ExplanationCompletenessEvaluation,
)
from qseries_v2.observation_intelligence.oi_051_oracle_explanation_delivery_model import (
    OI_051_REVISION,
    OracleExplanationDeliveryModelBuilder,
    verify_oracle_explanation_delivery_model,
)

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


def readout():
    return OracleExplanationReadout(
        query_id="query.test",
        query_kind="explanation",
        subject_hint="Astros strikeouts",
        headline="Oracle Evidence Explanation — Astros strikeouts",
        explanation_lines=("Fallback statement",),
        caveat_lines=(
            "structural association does not establish causation",
        ),
        built_at=NOW,
        readout_hash="a" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
        terminal_mutation_allowed=False,
    )


def ordering():
    return ExplanationEvidenceOrdering(
        query_id="query.test",
        items=(
            OrderedExplanationEvidenceItem(
                ordinal=1,
                subject="Astros strikeouts",
                status="partial",
                statement="Ordered explanation statement",
                evidence_count=2,
                context_role_count=3,
                relationship_type_count=1,
                order_hash="b" * 64,
            ),
        ),
        item_count=1,
        ordering_hash="c" * 64,
        read_only=True,
    )


def completeness():
    return ExplanationCompletenessEvaluation(
        query_id="query.test",
        status="partial",
        supported_count=0,
        partial_count=1,
        unsupported_count=0,
        ordered_item_count=1,
        reason_codes=("partial_explanation_candidates",),
        evaluation_hash="d" * 64,
        read_only=True,
    )


class TestOI051(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_delivery_model()
        )

    def test_build(self):
        model = OracleExplanationDeliveryModelBuilder().build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )

        self.assertEqual(
            model.completeness_status,
            "partial",
        )
        self.assertEqual(
            model.ordered_explanations,
            ("Ordered explanation statement",),
        )

    def test_caveats_merged(self):
        model = OracleExplanationDeliveryModelBuilder().build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )

        self.assertIn(
            "partial_explanation_candidates",
            model.caveats,
        )
        self.assertIn(
            "structural association does not establish causation",
            model.caveats,
        )

    def test_deterministic(self):
        builder = OracleExplanationDeliveryModelBuilder()

        a = builder.build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )
        b = builder.build(
            readout=readout(),
            ordering=ordering(),
            completeness=completeness(),
            delivered_at=NOW,
        )

        self.assertEqual(
            a.delivery_hash,
            b.delivery_hash,
        )

    def test_side_effects(self):
        item = OracleExplanationDeliveryModelBuilder()

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
    print(" OI-051 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION DELIVERY MODEL")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI051)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-051")
    print(f"[PASS] Revision: {OI_051_REVISION}")
    print("[PASS] Ordered explanation readout and completeness state merged into deterministic delivery model")
    print("[PASS] Explanation ordering, completeness status, caveats, and subject identity preserved")
    print("[PASS] Delivery remains read-only, terminal-safe, non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-051 CERTIFIED")
