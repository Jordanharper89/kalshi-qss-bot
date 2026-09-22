from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_019_evidence_contradiction_registry import (
    OI_019_REVISION,
    EvidenceRelationship,
    EvidenceContradictionRegistry,
    verify_evidence_contradiction_registry,
)


def relationship(
    relationship_id: str,
    left: str,
    right: str,
    relation: str,
):
    return EvidenceRelationship(
        relationship_id=relationship_id,
        left_evidence_id=left,
        right_evidence_id=right,
        relation=relation,
        basis="explicit certified evidence relationship",
    )


class TestOI019(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_evidence_contradiction_registry()
        )

    def test_registry(self):
        registry = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
                relationship(
                    "rel.2",
                    "obs.a",
                    "obs.c",
                    "agrees",
                ),
            )
        )
        self.assertEqual(
            len(registry.relationships),
            2,
        )

    def test_contradiction_query(self):
        registry = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        self.assertEqual(
            len(registry.by_relation("contradicts")),
            1,
        )

    def test_reverse_query(self):
        registry = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        self.assertEqual(
            len(registry.for_evidence("obs.a")),
            1,
        )

    def test_symmetric_identity(self):
        a = relationship(
            "rel.1",
            "obs.b",
            "obs.a",
            "agrees",
        )
        self.assertEqual(
            (a.left_evidence_id, a.right_evidence_id),
            ("obs.a", "obs.b"),
        )

    def test_self_rejected(self):
        with self.assertRaises(ValueError):
            relationship(
                "rel.bad",
                "obs.a",
                "obs.a",
                "agrees",
            )

    def test_deterministic(self):
        a = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        b = EvidenceContradictionRegistry(
            (
                relationship(
                    "rel.1",
                    "obs.a",
                    "obs.b",
                    "contradicts",
                ),
            )
        )
        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = EvidenceContradictionRegistry(())
        self.assertTrue(registry.read_only)
        self.assertFalse(registry.network_allowed)
        self.assertFalse(registry.persistence_allowed)
        self.assertFalse(registry.publication_allowed)
        self.assertFalse(registry.execution_allowed)
        self.assertFalse(registry.qseries_execution_allowed)
        self.assertFalse(registry.causal_inference_allowed)
        self.assertFalse(registry.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-019 CERTIFICATION TEST")
    print(" EVIDENCE CONTRADICTION REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI019
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-019")
    print(f"[PASS] Revision: {OI_019_REVISION}")
    print("[PASS] Agreement, contradiction, supersession, and independence relationships certified")
    print("[PASS] Evidence reverse queries and deterministic relationship identity certified")
    print("[PASS] No inferred contradiction, causal claim, or prediction introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-019 CERTIFIED")
