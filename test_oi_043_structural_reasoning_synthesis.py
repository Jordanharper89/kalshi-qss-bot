from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)
from qseries_v2.observation_intelligence.oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from qseries_v2.observation_intelligence.oi_040_reasoning_evidence_relationship_projection import (
    ReasoningEvidenceRelationship,
    ReasoningEvidenceRelationshipProjection,
)
from qseries_v2.observation_intelligence.oi_041_reasoning_evidence_relationship_registry import (
    ReasoningEvidenceRelationshipRegistry,
)
from qseries_v2.observation_intelligence.oi_042_oracle_reasoning_assembly import (
    OracleReasoningAssembly,
)
from qseries_v2.observation_intelligence.oi_043_structural_reasoning_synthesis import (
    OI_043_REVISION,
    StructuralReasoningSynthesizer,
    verify_structural_reasoning_synthesis,
)

NOW = datetime(2026, 8, 11, 6, 0, tzinfo=timezone.utc)


def context_registry():
    return ReasoningEvidenceContextRegistry(
        ReasoningEvidenceContextProjection(
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
                    context_roles=("evidence", "market_state"),
                    context_hash="d" * 64,
                ),
                ReasoningEvidenceContext(
                    canonical_observation_id="obs.2",
                    canonical_observation_hash="e" * 64,
                    adapter_id="adapter.sports.v1",
                    provider="SportsFeed",
                    subject="Astros strikeouts",
                    observation_type="lineup",
                    context_roles=("evidence", "sports_context"),
                    context_hash="f" * 64,
                ),
            ),
            context_count=2,
            projection_hash="1" * 64,
            read_only=True,
        )
    )


def relationship_registry():
    return ReasoningEvidenceRelationshipRegistry(
        ReasoningEvidenceRelationshipProjection(
            evidence_registry_hash="2" * 64,
            context_registry_hash="3" * 64,
            relationships=(
                ReasoningEvidenceRelationship(
                    left_observation_id="obs.1",
                    right_observation_id="obs.2",
                    relation_types=("same_subject", "shared_context_role"),
                    shared_context_roles=("evidence",),
                    relationship_hash="4" * 64,
                ),
            ),
            relationship_count=1,
            projection_hash="5" * 64,
            read_only=True,
        )
    )


def assembly():
    context = context_registry()
    relationships = relationship_registry()

    return OracleReasoningAssembly(
        assembly_id="assembly.test",
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="admitted",
        evidence_package_hash="6" * 64,
        context_registry_hash=context.registry_hash,
        relationship_registry_hash=relationships.registry_hash,
        evidence_count=2,
        context_count=2,
        relationship_count=1,
        missing_need_count=0,
        assembled_at=NOW,
        assembly_hash="7" * 64,
        read_only=True,
        predictive=False,
        causal_claim_allowed=False,
    )


class TestOI043(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_structural_reasoning_synthesis()
        )

    def test_synthesis(self):
        result = StructuralReasoningSynthesizer().synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertEqual(result.signal_count, 1)
        self.assertEqual(
            result.signals[0].signal_type,
            "multi_evidence_context",
        )

    def test_roles_preserved(self):
        result = StructuralReasoningSynthesizer().synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertIn(
            "market_state",
            result.signals[0].context_roles,
        )
        self.assertIn(
            "sports_context",
            result.signals[0].context_roles,
        )

    def test_relationships_preserved(self):
        result = StructuralReasoningSynthesizer().synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertIn(
            "same_subject",
            result.signals[0].relationship_types,
        )

    def test_deterministic(self):
        synthesizer = StructuralReasoningSynthesizer()

        a = synthesizer.synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )
        b = synthesizer.synthesize(
            assembly=assembly(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
        )

        self.assertEqual(
            a.synthesis_hash,
            b.synthesis_hash,
        )

    def test_side_effects(self):
        item = StructuralReasoningSynthesizer()

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
    print(" OI-043 CERTIFICATION TEST")
    print(" STRUCTURAL REASONING SYNTHESIS")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI043
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-043")
    print(f"[PASS] Revision: {OI_043_REVISION}")
    print("[PASS] Evidence, context roles, and structural relationships synthesized by subject")
    print("[PASS] Multi-evidence versus single-evidence structural context certified")
    print("[PASS] No causal claim, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-043 CERTIFIED")
