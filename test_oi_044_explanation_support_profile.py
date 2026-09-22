from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSignal,
    StructuralReasoningSynthesis,
)
from qseries_v2.observation_intelligence.oi_044_explanation_support_profile import (
    OI_044_REVISION,
    SUPPORT_MULTI,
    SUPPORT_SINGLE,
    ExplanationSupportProfiler,
    verify_explanation_support_profile,
)


def synthesis():
    return StructuralReasoningSynthesis(
        assembly_hash="a" * 64,
        signals=(
            StructuralReasoningSignal(
                signal_type="multi_evidence_context",
                subject="Astros strikeouts",
                evidence_observation_ids=("obs.1", "obs.2"),
                context_roles=("evidence", "market_state", "sports_context"),
                relationship_types=("same_subject",),
                signal_hash="b" * 64,
            ),
            StructuralReasoningSignal(
                signal_type="single_evidence_context",
                subject="Bitcoin",
                evidence_observation_ids=("obs.3",),
                context_roles=("evidence", "market_state"),
                relationship_types=(),
                signal_hash="c" * 64,
            ),
        ),
        signal_count=2,
        synthesis_hash="d" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI044(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_support_profile()
        )

    def test_profile(self):
        profile = ExplanationSupportProfiler().build(
            synthesis()
        )

        self.assertEqual(profile.item_count, 2)

    def test_multi_support(self):
        profile = ExplanationSupportProfiler().build(
            synthesis()
        )

        astros = tuple(
            item
            for item in profile.items
            if item.subject == "Astros strikeouts"
        )[0]

        self.assertEqual(
            astros.support_class,
            SUPPORT_MULTI,
        )

    def test_single_support(self):
        profile = ExplanationSupportProfiler().build(
            synthesis()
        )

        btc = tuple(
            item
            for item in profile.items
            if item.subject == "Bitcoin"
        )[0]

        self.assertEqual(
            btc.support_class,
            SUPPORT_SINGLE,
        )

    def test_deterministic(self):
        profiler = ExplanationSupportProfiler()

        a = profiler.build(synthesis())
        b = profiler.build(synthesis())

        self.assertEqual(
            a.profile_hash,
            b.profile_hash,
        )

    def test_side_effects(self):
        profiler = ExplanationSupportProfiler()

        self.assertTrue(profiler.read_only)
        self.assertFalse(profiler.network_allowed)
        self.assertFalse(profiler.persistence_allowed)
        self.assertFalse(profiler.publication_allowed)
        self.assertFalse(profiler.execution_allowed)
        self.assertFalse(profiler.qseries_execution_allowed)
        self.assertFalse(profiler.prediction_allowed)
        self.assertFalse(profiler.edge_score_allowed)
        self.assertFalse(profiler.probability_allowed)
        self.assertFalse(profiler.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-044 CERTIFICATION TEST")
    print(" EXPLANATION SUPPORT PROFILE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI044
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-044")
    print(f"[PASS] Revision: {OI_044_REVISION}")
    print("[PASS] Structural explanation support classified without probability or edge scoring")
    print("[PASS] Single-evidence and multi-evidence support states certified")
    print("[PASS] Support classification is descriptive only and does not establish causation")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-044 CERTIFIED")
