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
from qseries_v2.observation_intelligence.oi_020_temporal_association import (
    TemporalAssociation,
)
from qseries_v2.observation_intelligence.oi_021_explanation_candidate_assembly import (
    OI_021_REVISION,
    ExplanationCandidateAssembler,
    verify_explanation_candidate_assembly,
)

NOW = datetime(
    2026,
    8,
    10,
    15,
    0,
    tzinfo=timezone.utc,
)


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


def association(
    evidence_id: str,
    seconds: int,
):
    return TemporalAssociation(
        change_hash="c" * 64,
        evidence_observation_id=evidence_id,
        evidence_subject="Astros",
        evidence_observation_type="news",
        evidence_observed_at=NOW,
        seconds_from_change_observation=seconds,
        temporal_relation=(
            "before"
            if seconds < 0
            else (
                "after"
                if seconds > 0
                else "simultaneous"
            )
        ),
        association_hash="e" * 64,
    )


def registry():
    return EvidenceContradictionRegistry(
        (
            EvidenceRelationship(
                relationship_id="rel.1",
                left_evidence_id="obs.a",
                right_evidence_id="obs.b",
                relation="contradicts",
                basis="explicit source disagreement",
            ),
        )
    )


class TestOI021(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_explanation_candidate_assembly()
        )

    def test_assembly(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(
                    association(
                        "obs.a",
                        -20,
                    ),
                    association(
                        "obs.b",
                        -10,
                    ),
                ),
                evidence_relationships=registry(),
            )
        )

        self.assertEqual(
            len(values.candidates),
            2,
        )

    def test_nearest_first(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(
                    association(
                        "obs.a",
                        -20,
                    ),
                    association(
                        "obs.b",
                        -10,
                    ),
                ),
                evidence_relationships=registry(),
            )
        )

        self.assertEqual(
            values.candidates[0]
            .evidence_observation_id,
            "obs.b",
        )

    def test_contradiction_count(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(
                    association(
                        "obs.a",
                        -20,
                    ),
                ),
                evidence_relationships=registry(),
            )
        )

        self.assertEqual(
            values.candidates[0]
            .contradiction_count,
            1,
        )

    def test_non_causal(self):
        values = (
            ExplanationCandidateAssembler()
            .assemble(
                package=package(),
                temporal_associations=(),
                evidence_relationships=registry(),
            )
        )

        self.assertFalse(
            values.causal_claim_allowed
        )
        self.assertFalse(
            values.predictive
        )
        self.assertFalse(
            values.edge_score_allowed
        )

    def test_deterministic(self):
        assembler = ExplanationCandidateAssembler()

        a = assembler.assemble(
            package=package(),
            temporal_associations=(
                association(
                    "obs.a",
                    -20,
                ),
            ),
            evidence_relationships=registry(),
        )

        b = assembler.assemble(
            package=package(),
            temporal_associations=(
                association(
                    "obs.a",
                    -20,
                ),
            ),
            evidence_relationships=registry(),
        )

        self.assertEqual(
            a.candidate_set_hash,
            b.candidate_set_hash,
        )

    def test_side_effects(self):
        assembler = ExplanationCandidateAssembler()

        self.assertTrue(
            assembler.read_only
        )
        self.assertFalse(
            assembler.network_allowed
        )
        self.assertFalse(
            assembler.persistence_allowed
        )
        self.assertFalse(
            assembler.publication_allowed
        )
        self.assertFalse(
            assembler.execution_allowed
        )
        self.assertFalse(
            assembler.qseries_execution_allowed
        )
        self.assertFalse(
            assembler.causal_claim_allowed
        )
        self.assertFalse(
            assembler.prediction_allowed
        )
        self.assertFalse(
            assembler.edge_score_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-021 CERTIFICATION TEST")
    print(" EXPLANATION CANDIDATE ASSEMBLY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI021
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-021")
    print(f"[PASS] Revision: {OI_021_REVISION}")
    print("[PASS] Temporally associated evidence assembled into explanation candidates")
    print("[PASS] Agreement and contradiction context preserved per candidate")
    print("[PASS] Candidate ordering is structural and does not imply causal importance")
    print("[PASS] Causal claims, prediction, and edge scoring remain disabled")
    print("[DONE] OI-021 CERTIFIED")
