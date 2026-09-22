from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_042_oracle_reasoning_assembly import (
    OracleReasoningAssembly,
)
from qseries_v2.observation_intelligence.oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSignal,
    StructuralReasoningSynthesis,
)
from qseries_v2.observation_intelligence.oi_044_explanation_support_profile import (
    ExplanationSupportItem,
    ExplanationSupportProfile,
)
from qseries_v2.observation_intelligence.oi_045_oracle_reasoning_read_model import (
    OI_045_REVISION,
    OracleReasoningReadModelBuilder,
    verify_oracle_reasoning_read_model,
)

NOW = datetime(2026, 8, 11, 7, 0, tzinfo=timezone.utc)


def assembly():
    return OracleReasoningAssembly(
        assembly_id="assembly.test",
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="partial",
        evidence_package_hash="a" * 64,
        context_registry_hash="b" * 64,
        relationship_registry_hash="c" * 64,
        evidence_count=2,
        context_count=2,
        relationship_count=1,
        missing_need_count=1,
        assembled_at=NOW,
        assembly_hash="d" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


def synthesis():
    return StructuralReasoningSynthesis(
        assembly_hash="d" * 64,
        signals=(
            StructuralReasoningSignal(
                signal_type="multi_evidence_context",
                subject="Astros strikeouts",
                evidence_observation_ids=("obs.1", "obs.2"),
                context_roles=(
                    "evidence",
                    "market_state",
                    "sports_context",
                ),
                relationship_types=(
                    "same_subject",
                ),
                signal_hash="e" * 64,
            ),
        ),
        signal_count=1,
        synthesis_hash="f" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


def support_profile():
    return ExplanationSupportProfile(
        synthesis_hash="f" * 64,
        items=(
            ExplanationSupportItem(
                subject="Astros strikeouts",
                support_class="multi_evidence_structure",
                evidence_count=2,
                context_role_count=3,
                relationship_type_count=1,
                support_hash="1" * 64,
            ),
        ),
        item_count=1,
        profile_hash="2" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI045(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_reasoning_read_model()
        )

    def test_build(self):
        model = OracleReasoningReadModelBuilder().build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(model.evidence_count, 2)
        self.assertEqual(model.relationship_count, 1)
        self.assertEqual(model.missing_need_count, 1)
        self.assertEqual(len(model.items), 1)

    def test_support_preserved(self):
        model = OracleReasoningReadModelBuilder().build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(
            model.items[0].support_class,
            "multi_evidence_structure",
        )

    def test_partial_preserved(self):
        model = OracleReasoningReadModelBuilder().build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(
            model.admission_status,
            "partial",
        )
        self.assertEqual(
            model.missing_need_count,
            1,
        )

    def test_deterministic(self):
        builder = OracleReasoningReadModelBuilder()

        a = builder.build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )
        b = builder.build(
            assembly=assembly(),
            synthesis=synthesis(),
            support_profile=support_profile(),
            built_at=NOW,
        )

        self.assertEqual(
            a.read_model_hash,
            b.read_model_hash,
        )

    def test_side_effects(self):
        builder = OracleReasoningReadModelBuilder()

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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-045 CERTIFICATION TEST")
    print(" ORACLE REASONING READ MODEL")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI045
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-045")
    print(f"[PASS] Revision: {OI_045_REVISION}")
    print("[PASS] Structural reasoning and explanation-support state exposed through deterministic Oracle read model")
    print("[PASS] Evidence count, relationships, admission status, and missing evidence preserved")
    print("[PASS] Read model remains non-causal, non-predictive, non-scoring, and read-only")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-045 CERTIFIED")
