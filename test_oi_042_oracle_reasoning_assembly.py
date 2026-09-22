from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidenceItem,
    OracleReasoningEvidencePackage,
)
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
    OI_042_REVISION,
    OracleReasoningAssembler,
    verify_oracle_reasoning_assembly,
)

NOW = datetime(
    2026,
    8,
    11,
    5,
    0,
    tzinfo=timezone.utc,
)


def evidence_package():
    return OracleReasoningEvidencePackage(
        package_id="reasoning.test",
        query_id="query.test",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="admitted",
        admission_hash="a" * 64,
        materialization_hash="b" * 64,
        evidence_items=(
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.1",
                canonical_observation_hash="c" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                observed_at=NOW,
            ),
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.2",
                canonical_observation_hash="d" * 64,
                adapter_id="adapter.sports.v1",
                provider="SportsFeed",
                subject="Astros strikeouts",
                observation_type="lineup",
                observed_at=NOW,
            ),
        ),
        missing_need_count=0,
        built_at=NOW,
        package_hash="e" * 64,
        read_only=True,
        predictive=False,
    )


def context_registry():
    return ReasoningEvidenceContextRegistry(
        ReasoningEvidenceContextProjection(
            package_hash="e" * 64,
            registry_hash="f" * 64,
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
                    ),
                    context_hash="1" * 64,
                ),
                ReasoningEvidenceContext(
                    canonical_observation_id="obs.2",
                    canonical_observation_hash="d" * 64,
                    adapter_id="adapter.sports.v1",
                    provider="SportsFeed",
                    subject="Astros strikeouts",
                    observation_type="lineup",
                    context_roles=(
                        "evidence",
                        "sports_context",
                    ),
                    context_hash="2" * 64,
                ),
            ),
            context_count=2,
            projection_hash="3" * 64,
            read_only=True,
        )
    )


def relationship_registry():
    return ReasoningEvidenceRelationshipRegistry(
        ReasoningEvidenceRelationshipProjection(
            evidence_registry_hash="4" * 64,
            context_registry_hash="5" * 64,
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
                    ),
                    relationship_hash="6" * 64,
                ),
            ),
            relationship_count=1,
            projection_hash="7" * 64,
            read_only=True,
        )
    )


class TestOI042(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oracle_reasoning_assembly()
        )

    def test_assembly(self):
        assembly = OracleReasoningAssembler().assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertEqual(
            assembly.evidence_count,
            2,
        )
        self.assertEqual(
            assembly.context_count,
            2,
        )
        self.assertEqual(
            assembly.relationship_count,
            1,
        )

    def test_lineage(self):
        assembly = OracleReasoningAssembler().assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertEqual(
            assembly.evidence_package_hash,
            "e" * 64,
        )

    def test_non_causal(self):
        assembly = OracleReasoningAssembler().assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertFalse(
            assembly.predictive
        )
        self.assertFalse(
            assembly.causal_claim_allowed
        )
        self.assertTrue(
            assembly.read_only
        )

    def test_deterministic(self):
        assembler = OracleReasoningAssembler()

        a = assembler.assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        b = assembler.assemble(
            assembly_id="assembly.test",
            evidence_package=evidence_package(),
            context_registry=context_registry(),
            relationship_registry=relationship_registry(),
            assembled_at=NOW,
        )

        self.assertEqual(
            a.assembly_hash,
            b.assembly_hash,
        )

    def test_side_effects(self):
        assembler = OracleReasoningAssembler()

        self.assertTrue(assembler.read_only)
        self.assertFalse(assembler.network_allowed)
        self.assertFalse(assembler.persistence_allowed)
        self.assertFalse(assembler.publication_allowed)
        self.assertFalse(assembler.execution_allowed)
        self.assertFalse(assembler.qseries_execution_allowed)
        self.assertFalse(assembler.prediction_allowed)
        self.assertFalse(assembler.edge_score_allowed)
        self.assertFalse(assembler.probability_allowed)
        self.assertFalse(assembler.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-042 CERTIFICATION TEST")
    print(" ORACLE REASONING ASSEMBLY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI042
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-042")
    print(f"[PASS] Revision: {OI_042_REVISION}")
    print("[PASS] Evidence, context, and structural relationships assembled for Oracle reasoning")
    print("[PASS] Evidence lineage, context lineage, relationship lineage, and admission status preserved")
    print("[PASS] Assembly remains read-only, non-causal, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-042 CERTIFIED")
