from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)
from qseries_v2.observation_intelligence.oi_039_reasoning_evidence_context_registry import (
    OI_039_REVISION,
    ReasoningEvidenceContextRegistry,
    verify_reasoning_evidence_context_registry,
)


def projection():
    return ReasoningEvidenceContextProjection(
        package_hash="a" * 64,
        registry_hash="b" * 64,
        contexts=(
            ReasoningEvidenceContext(
                canonical_observation_id="obs.1",
                canonical_observation_hash="c" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                context_roles=(
                    "evidence",
                    "market_state",
                    "source_context",
                ),
                context_hash="d" * 64,
            ),
            ReasoningEvidenceContext(
                canonical_observation_id="obs.2",
                canonical_observation_hash="e" * 64,
                adapter_id="adapter.sports.v1",
                provider="SportsFeed",
                subject="Astros",
                observation_type="lineup",
                context_roles=(
                    "evidence",
                    "source_context",
                    "sports_context",
                ),
                context_hash="f" * 64,
            ),
        ),
        context_count=2,
        projection_hash="1" * 64,
        read_only=True,
    )


class TestOI039(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_context_registry()
        )

    def test_registry(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            len(registry.contexts),
            2,
        )

    def test_get(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            registry.get("obs.1").provider,
            "Kalshi",
        )

    def test_role_query(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_role(
                    "market_state"
                )
            ),
            1,
        )

        self.assertEqual(
            len(
                registry.by_role(
                    "sports_context"
                )
            ),
            1,
        )

    def test_reverse_queries(self):
        registry = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            len(
                registry.by_adapter(
                    "adapter.kalshi.v1"
                )
            ),
            1,
        )

        self.assertEqual(
            len(
                registry.by_subject(
                    "Astros"
                )
            ),
            1,
        )

    def test_deterministic(self):
        a = ReasoningEvidenceContextRegistry(
            projection()
        )

        b = ReasoningEvidenceContextRegistry(
            projection()
        )

        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = ReasoningEvidenceContextRegistry(
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
    print(" OI-039 CERTIFICATION TEST")
    print(" REASONING EVIDENCE CONTEXT REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI039
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-039")
    print(f"[PASS] Revision: {OI_039_REVISION}")
    print("[PASS] Reasoning evidence context registry certified")
    print("[PASS] Context queries by identity, role, adapter, and subject certified")
    print("[PASS] Context remains structural, read-only, non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-039 CERTIFIED")
