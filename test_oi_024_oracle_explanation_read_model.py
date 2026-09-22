from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_022_evidence_narrative_assembly import (
    NarrativeEvidenceEntry,
    EvidenceNarrative,
)
from qseries_v2.observation_intelligence.oi_023_evidence_confidence_composition import (
    EvidenceConfidenceProfile,
)
from qseries_v2.observation_intelligence.oi_024_oracle_explanation_read_model import (
    OI_024_REVISION,
    OracleExplanationReadModelBuilder,
    verify_oracle_explanation_read_model,
)

NOW = datetime(
    2026,
    8,
    10,
    17,
    0,
    tzinfo=timezone.utc,
)


def package():
    return ExplanationEvidencePackage(
        query_id="query.astros",
        profile_id="profile.market_explanation",
        built_at=NOW,
        reasoning_input_hash="a" * 64,
        sufficiency_decision_hash="b" * 64,
        sufficient_evidence=True,
        evidence_item_count=2,
        change_hashes=("c" * 64,),
        package_hash="d" * 64,
        causal_claim_allowed=False,
        predictive=False,
        read_only=True,
    )


def narrative():
    return EvidenceNarrative(
        package_hash="d" * 64,
        candidate_set_hash="e" * 64,
        entries=(
            NarrativeEvidenceEntry(
                ordinal=1,
                evidence_observation_id="obs.a",
                temporal_relation="before",
                seconds_from_change_observation=-20,
                agreement_count=1,
                contradiction_count=0,
                entry_hash="f" * 64,
            ),
        ),
        supporting_relationship_count=1,
        contradicting_relationship_count=0,
        narrative_hash="1" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
        read_only=True,
    )


def confidence():
    return EvidenceConfidenceProfile(
        sufficiency_decision_hash="b" * 64,
        narrative_hash="1" * 64,
        evidence_item_count=2,
        distinct_source_count=2,
        stale_evidence_count=0,
        supporting_relationship_count=1,
        contradicting_relationship_count=0,
        completeness_status="complete",
        confidence_hash="2" * 64,
        predictive=False,
        edge_score_allowed=False,
        probability_allowed=False,
        read_only=True,
    )


class TestOI024(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_explanation_read_model()
        )

    def test_build(self):
        model = OracleExplanationReadModelBuilder().build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertEqual(
            model.query_id,
            "query.astros",
        )

        self.assertEqual(
            model.completeness_status,
            "complete",
        )

        self.assertEqual(
            len(model.timeline),
            1,
        )

    def test_counts(self):
        model = OracleExplanationReadModelBuilder().build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertEqual(
            model.evidence_item_count,
            2,
        )

        self.assertEqual(
            model.distinct_source_count,
            2,
        )

        self.assertEqual(
            model.supporting_relationship_count,
            1,
        )

    def test_non_predictive(self):
        model = OracleExplanationReadModelBuilder().build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertFalse(
            model.causal_claim_allowed
        )

        self.assertFalse(
            model.predictive
        )

        self.assertFalse(
            model.edge_score_allowed
        )

        self.assertFalse(
            model.probability_allowed
        )

        self.assertTrue(
            model.read_only
        )

    def test_deterministic(self):
        builder = OracleExplanationReadModelBuilder()

        a = builder.build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        b = builder.build(
            package=package(),
            narrative=narrative(),
            confidence=confidence(),
            built_at=NOW,
        )

        self.assertEqual(
            a.read_model_hash,
            b.read_model_hash,
        )

    def test_side_effects(self):
        builder = OracleExplanationReadModelBuilder()

        self.assertTrue(
            builder.read_only
        )

        self.assertFalse(
            builder.network_allowed
        )

        self.assertFalse(
            builder.persistence_allowed
        )

        self.assertFalse(
            builder.publication_allowed
        )

        self.assertFalse(
            builder.execution_allowed
        )

        self.assertFalse(
            builder.qseries_execution_allowed
        )

        self.assertFalse(
            builder.causal_claim_allowed
        )

        self.assertFalse(
            builder.prediction_allowed
        )

        self.assertFalse(
            builder.edge_score_allowed
        )

        self.assertFalse(
            builder.probability_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-024 CERTIFICATION TEST")
    print(" ORACLE EXPLANATION READ MODEL")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI024
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-024")
    print(f"[PASS] Revision: {OI_024_REVISION}")
    print("[PASS] Explanation-ready Oracle read model certified")
    print("[PASS] Timeline, evidence completeness, source diversity, freshness, support, and contradiction preserved")
    print("[PASS] Causal claims, prediction probability, and edge scoring remain disabled")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-024 CERTIFIED")
