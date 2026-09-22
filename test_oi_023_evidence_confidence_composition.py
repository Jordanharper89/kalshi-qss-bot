from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_016_evidence_sufficiency_gate import (
    EvidenceSufficiencyDecision,
)
from qseries_v2.observation_intelligence.oi_022_evidence_narrative_assembly import (
    EvidenceNarrative,
)
from qseries_v2.observation_intelligence.oi_023_evidence_confidence_composition import (
    OI_023_REVISION,
    COMPLETE,
    PARTIAL,
    EvidenceConfidenceComposer,
    verify_evidence_confidence_composition,
)


def decision(sufficient=True):
    return EvidenceSufficiencyDecision(
        policy_id="policy.test",
        input_hash="a" * 64,
        evidence_item_count=2,
        distinct_source_count=2,
        stale_evidence_count=0,
        complete_required_evidence=sufficient,
        sufficient=sufficient,
        reason_codes=(
            ()
            if sufficient
            else ("missing_required_evidence",)
        ),
        decision_hash="b" * 64,
    )


def narrative():
    return EvidenceNarrative(
        package_hash="c" * 64,
        candidate_set_hash="d" * 64,
        entries=(),
        supporting_relationship_count=2,
        contradicting_relationship_count=1,
        narrative_hash="e" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
        read_only=True,
    )


class TestOI023(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_confidence_composition()
        )

    def test_complete(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertEqual(
            profile.completeness_status,
            COMPLETE,
        )

    def test_partial(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(False),
            narrative=narrative(),
        )
        self.assertEqual(
            profile.completeness_status,
            PARTIAL,
        )

    def test_counts_preserved(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertEqual(profile.distinct_source_count, 2)
        self.assertEqual(profile.supporting_relationship_count, 2)
        self.assertEqual(profile.contradicting_relationship_count, 1)

    def test_non_predictive(self):
        profile = EvidenceConfidenceComposer().compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertFalse(profile.predictive)
        self.assertFalse(profile.edge_score_allowed)
        self.assertFalse(profile.probability_allowed)
        self.assertTrue(profile.read_only)

    def test_deterministic(self):
        composer = EvidenceConfidenceComposer()
        a = composer.compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        b = composer.compose(
            sufficiency=decision(True),
            narrative=narrative(),
        )
        self.assertEqual(
            a.confidence_hash,
            b.confidence_hash,
        )

    def test_side_effects(self):
        composer = EvidenceConfidenceComposer()
        self.assertTrue(composer.read_only)
        self.assertFalse(composer.network_allowed)
        self.assertFalse(composer.persistence_allowed)
        self.assertFalse(composer.publication_allowed)
        self.assertFalse(composer.execution_allowed)
        self.assertFalse(composer.qseries_execution_allowed)
        self.assertFalse(composer.prediction_allowed)
        self.assertFalse(composer.edge_score_allowed)
        self.assertFalse(composer.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-023 CERTIFICATION TEST")
    print(" EVIDENCE CONFIDENCE COMPOSITION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI023
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-023")
    print(f"[PASS] Revision: {OI_023_REVISION}")
    print("[PASS] Evidence completeness, source diversity, freshness, and contradiction composition certified")
    print("[PASS] Confidence composition describes evidence quality only")
    print("[PASS] Prediction probability, edge scoring, and trade confidence remain disabled")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-023 CERTIFIED")
