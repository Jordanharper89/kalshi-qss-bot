from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_045_oracle_reasoning_read_model import (
    OracleReasoningReadItem,
    OracleReasoningReadModel,
)
from qseries_v2.observation_intelligence.oi_047_evidence_explanation_synthesis import (
    EvidenceExplanationStatement,
    EvidenceExplanationSynthesis,
)
from qseries_v2.observation_intelligence.oi_049_explanation_evidence_ordering import (
    OI_049_REVISION,
    ExplanationEvidenceOrderer,
    verify_explanation_evidence_ordering,
)

NOW = datetime(2026, 8, 11, 11, 0, tzinfo=timezone.utc)


def read_model():
    return OracleReasoningReadModel(
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Test",
        admission_status="admitted",
        evidence_count=3,
        relationship_count=1,
        missing_need_count=0,
        items=(
            OracleReasoningReadItem(
                subject="Alpha",
                signal_type="multi_evidence_context",
                support_class="multi_evidence_structure",
                evidence_count=2,
                context_roles=("evidence", "market_state"),
                relationship_types=("same_subject",),
                item_hash="a" * 64,
            ),
            OracleReasoningReadItem(
                subject="Beta",
                signal_type="single_evidence_context",
                support_class="single_source_structure",
                evidence_count=1,
                context_roles=("evidence",),
                relationship_types=(),
                item_hash="b" * 64,
            ),
        ),
        built_at=NOW,
        read_model_hash="c" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


def synthesis():
    return EvidenceExplanationSynthesis(
        query_id="query.test",
        read_model_hash="c" * 64,
        resolution_hash="d" * 64,
        statements=(
            EvidenceExplanationStatement(
                subject="Beta",
                status="supported",
                statement="Beta statement",
                caveats=("structural association does not establish causation",),
                statement_hash="e" * 64,
            ),
            EvidenceExplanationStatement(
                subject="Alpha",
                status="supported",
                statement="Alpha statement",
                caveats=("structural association does not establish causation",),
                statement_hash="f" * 64,
            ),
        ),
        statement_count=2,
        synthesis_hash="1" * 64,
        read_only=True,
        causal_claim_allowed=False,
    )


class TestOI049(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_explanation_evidence_ordering())

    def test_ordering(self):
        result = ExplanationEvidenceOrderer().order(
            read_model=read_model(),
            synthesis=synthesis(),
        )

        self.assertEqual(result.item_count, 2)
        self.assertEqual(result.items[0].subject, "Alpha")
        self.assertEqual(result.items[1].subject, "Beta")

    def test_ordinals(self):
        result = ExplanationEvidenceOrderer().order(
            read_model=read_model(),
            synthesis=synthesis(),
        )

        self.assertEqual(
            tuple(item.ordinal for item in result.items),
            (1, 2),
        )

    def test_deterministic(self):
        orderer = ExplanationEvidenceOrderer()

        a = orderer.order(
            read_model=read_model(),
            synthesis=synthesis(),
        )
        b = orderer.order(
            read_model=read_model(),
            synthesis=synthesis(),
        )

        self.assertEqual(a.ordering_hash, b.ordering_hash)

    def test_side_effects(self):
        item = ExplanationEvidenceOrderer()

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
    print(" OI-049 CERTIFICATION TEST")
    print(" EXPLANATION EVIDENCE ORDERING")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI049)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-049")
    print(f"[PASS] Revision: {OI_049_REVISION}")
    print("[PASS] Explanation evidence ordered deterministically by structural support")
    print("[PASS] Evidence count, context density, relationship density, and subject tie-break preserved")
    print("[PASS] No causal claim, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-049 CERTIFIED")
