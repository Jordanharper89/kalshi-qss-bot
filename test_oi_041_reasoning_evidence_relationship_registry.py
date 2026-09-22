from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_040_reasoning_evidence_relationship_projection import (
    ReasoningEvidenceRelationship,
    ReasoningEvidenceRelationshipProjection,
)
from qseries_v2.observation_intelligence.oi_041_reasoning_evidence_relationship_registry import (
    OI_041_REVISION,
    ReasoningEvidenceRelationshipRegistry,
    verify_reasoning_evidence_relationship_registry,
)


def projection():
    return ReasoningEvidenceRelationshipProjection(
        evidence_registry_hash="a" * 64,
        context_registry_hash="b" * 64,
        relationships=(
            ReasoningEvidenceRelationship(
                left_observation_id="obs.1",
                right_observation_id="obs.2",
                relation_types=(
                    "same_subject",
                    "shared_context_role",
                ),
                shared_context_roles=(
                    "evidence",
                    "source_context",
                ),
                relationship_hash="c" * 64,
            ),
        ),
        relationship_count=1,
        projection_hash="d" * 64,
        read_only=True,
    )


class TestOI041(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_relationship_registry()
        )

    def test_registry(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(registry.relationships),
            1,
        )

    def test_observation_query(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_observation(
                    "obs.1"
                )
            ),
            1,
        )

    def test_relation_query(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_relation(
                    "same_subject"
                )
            ),
            1,
        )

    def test_context_role_query(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_shared_context_role(
                    "evidence"
                )
            ),
            1,
        )

    def test_unknown(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            registry.by_observation(
                "obs.unknown"
            ),
            (),
        )

    def test_deterministic(self):
        a = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        b = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = ReasoningEvidenceRelationshipRegistry(
            projection()
        )

        self.assertTrue(registry.read_only)
        self.assertFalse(registry.network_allowed)
        self.assertFalse(registry.persistence_allowed)
        self.assertFalse(registry.publication_allowed)
        self.assertFalse(registry.execution_allowed)
        self.assertFalse(registry.qseries_execution_allowed)
        self.assertFalse(registry.prediction_allowed)
        self.assertFalse(registry.edge_score_allowed)
        self.assertFalse(registry.probability_allowed)
        self.assertFalse(registry.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-041 CERTIFICATION TEST")
    print(" REASONING EVIDENCE RELATIONSHIP REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI041
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-041")
    print(f"[PASS] Revision: {OI_041_REVISION}")
    print("[PASS] Structural evidence relationship registry certified")
    print("[PASS] Reverse queries by observation, relationship type, and shared context role certified")
    print("[PASS] Registry remains deterministic, read-only, structural, and non-causal")
    print("[PASS] Network, persistence, publication, prediction, scoring, and execution disabled")
    print("[DONE] OI-041 CERTIFIED")
