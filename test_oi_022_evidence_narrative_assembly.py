from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_019_evidence_contradiction_registry import (
    EvidenceRelationship,
    EvidenceContradictionRegistry,
)
from qseries_v2.observation_intelligence.oi_021_explanation_candidate_assembly import (
    ExplanationCandidate,
    ExplanationCandidateSet,
)
from qseries_v2.observation_intelligence.oi_022_evidence_narrative_assembly import (
    OI_022_REVISION,
    EvidenceNarrativeAssembler,
    verify_evidence_narrative_assembly,
)

NOW = datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)


def package():
    return ExplanationEvidencePackage(
        query_id="query.explain",
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


def candidate_set():
    return ExplanationCandidateSet(
        package_hash="d" * 64,
        candidates=(
            ExplanationCandidate(
                evidence_observation_id="obs.a",
                temporal_relation="before",
                seconds_from_change_observation=-30,
                contradiction_count=1,
                agreement_count=0,
                candidate_hash="e" * 64,
            ),
            ExplanationCandidate(
                evidence_observation_id="obs.b",
                temporal_relation="before",
                seconds_from_change_observation=-10,
                contradiction_count=0,
                agreement_count=1,
                candidate_hash="f" * 64,
            ),
        ),
        candidate_set_hash="1" * 64,
        causal_claim_allowed=False,
        predictive=False,
        edge_score_allowed=False,
    )


def registry():
    return EvidenceContradictionRegistry(
        (
            EvidenceRelationship(
                relationship_id="rel.1",
                left_evidence_id="obs.a",
                right_evidence_id="obs.b",
                relation="contradicts",
                basis="explicit disagreement",
            ),
        )
    )


class TestOI022(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_evidence_narrative_assembly())

    def test_assembly(self):
        narrative = EvidenceNarrativeAssembler().assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertEqual(len(narrative.entries), 2)
        self.assertEqual(narrative.contradicting_relationship_count, 1)

    def test_order_preserved(self):
        narrative = EvidenceNarrativeAssembler().assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertEqual(
            tuple(item.ordinal for item in narrative.entries),
            (1, 2),
        )

    def test_non_causal(self):
        narrative = EvidenceNarrativeAssembler().assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertFalse(narrative.causal_claim_allowed)
        self.assertFalse(narrative.predictive)
        self.assertFalse(narrative.edge_score_allowed)
        self.assertTrue(narrative.read_only)

    def test_deterministic(self):
        assembler = EvidenceNarrativeAssembler()
        a = assembler.assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        b = assembler.assemble(
            package=package(),
            candidates=candidate_set(),
            relationships=registry(),
        )
        self.assertEqual(a.narrative_hash, b.narrative_hash)

    def test_side_effects(self):
        assembler = EvidenceNarrativeAssembler()
        self.assertTrue(assembler.read_only)
        self.assertFalse(assembler.network_allowed)
        self.assertFalse(assembler.persistence_allowed)
        self.assertFalse(assembler.publication_allowed)
        self.assertFalse(assembler.execution_allowed)
        self.assertFalse(assembler.qseries_execution_allowed)
        self.assertFalse(assembler.causal_claim_allowed)
        self.assertFalse(assembler.prediction_allowed)
        self.assertFalse(assembler.edge_score_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-022 CERTIFICATION TEST")
    print(" EVIDENCE NARRATIVE ASSEMBLY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestOI022)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-022")
    print(f"[PASS] Revision: {OI_022_REVISION}")
    print("[PASS] Explanation candidates assembled into deterministic evidence narrative")
    print("[PASS] Chronology, agreement, and contradiction context preserved")
    print("[PASS] Narrative remains non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-022 CERTIFIED")
