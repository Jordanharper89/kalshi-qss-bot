from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_045_oracle_reasoning_read_model import (
    OracleReasoningReadItem,
    OracleReasoningReadModel,
)
from qseries_v2.observation_intelligence.oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
    ExplanationCandidateResolutionItem,
)
from qseries_v2.observation_intelligence.oi_047_evidence_explanation_synthesis import (
    OI_047_REVISION,
    EvidenceExplanationSynthesizer,
    verify_evidence_explanation_synthesis,
)

NOW = datetime(2026, 8, 11, 9, 0, tzinfo=timezone.utc)


def read_model():
    return OracleReasoningReadModel(
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="partial",
        evidence_count=2,
        relationship_count=1,
        missing_need_count=1,
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


def resolution():
    return ExplanationCandidateResolution(
        query_id="query.test",
        read_model_hash="b" * 64,
        items=(
            ExplanationCandidateResolutionItem(
                subject="Astros strikeouts",
                status="partial",
                evidence_count=2,
                support_class="multi_evidence_structure",
                context_roles=(
                    "evidence",
                    "market_state",
                    "sports_context",
                ),
                relationship_types=(
                    "same_subject",
                ),
                reason_codes=(
                    "missing_required_evidence",
                ),
                item_hash="c" * 64,
            ),
        ),
        supported_count=0,
        partial_count=1,
        unsupported_count=0,
        resolution_hash="d" * 64,
        read_only=True,
    )


class TestOI047(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_explanation_synthesis()
        )

    def test_synthesis(self):
        result = EvidenceExplanationSynthesizer().synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertEqual(
            result.statement_count,
            1,
        )

        self.assertIn(
            "Astros strikeouts",
            result.statements[0].statement,
        )

    def test_partial_caveat(self):
        result = EvidenceExplanationSynthesizer().synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertIn(
            "explanation is incomplete",
            result.statements[0].caveats,
        )

    def test_non_causal(self):
        result = EvidenceExplanationSynthesizer().synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertFalse(
            result.causal_claim_allowed
        )

    def test_deterministic(self):
        synthesizer = EvidenceExplanationSynthesizer()

        a = synthesizer.synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        b = synthesizer.synthesize(
            read_model=read_model(),
            resolution=resolution(),
        )

        self.assertEqual(
            a.synthesis_hash,
            b.synthesis_hash,
        )

    def test_side_effects(self):
        item = EvidenceExplanationSynthesizer()

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
    print(" OI-047 CERTIFICATION TEST")
    print(" EVIDENCE EXPLANATION SYNTHESIS")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI047
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-047")
    print(f"[PASS] Revision: {OI_047_REVISION}")
    print("[PASS] Structural reasoning converted into deterministic evidence-grounded explanation statements")
    print("[PASS] Partial explanation state and caveats remain explicit")
    print("[PASS] Association is not promoted to causation, prediction, probability, or edge")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-047 CERTIFIED")
