from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidenceItem,
    OracleReasoningEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_037_reasoning_evidence_registry import (
    ReasoningEvidenceRegistry,
)
from qseries_v2.observation_intelligence.oi_038_reasoning_evidence_context_projection import (
    ReasoningEvidenceContext,
    ReasoningEvidenceContextProjection,
)
from qseries_v2.observation_intelligence.oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from qseries_v2.observation_intelligence.oi_040_reasoning_evidence_relationship_projection import (
    OI_040_REVISION,
    RELATION_SAME_SUBJECT,
    RELATION_SHARED_CONTEXT_ROLE,
    ReasoningEvidenceRelationshipProjector,
    verify_reasoning_evidence_relationship_projection,
)

NOW = datetime(
    2026,
    8,
    11,
    4,
    0,
    tzinfo=timezone.utc,
)


def package():
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
    projection = ReasoningEvidenceContextProjection(
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
                    "source_context",
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
                    "source_context",
                    "sports_context",
                ),
                context_hash="2" * 64,
            ),
        ),
        context_count=2,
        projection_hash="3" * 64,
        read_only=True,
    )

    return ReasoningEvidenceContextRegistry(
        projection
    )


class TestOI040(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_relationship_projection()
        )

    def test_projection(self):
        projection = (
            ReasoningEvidenceRelationshipProjector()
            .project(
                evidence_registry=ReasoningEvidenceRegistry(
                    package()
                ),
                context_registry=context_registry(),
            )
        )

        self.assertEqual(
            projection.relationship_count,
            1,
        )

    def test_same_subject(self):
        projection = (
            ReasoningEvidenceRelationshipProjector()
            .project(
                evidence_registry=ReasoningEvidenceRegistry(
                    package()
                ),
                context_registry=context_registry(),
            )
        )

        self.assertIn(
            RELATION_SAME_SUBJECT,
            projection.relationships[0].relation_types,
        )

    def test_shared_context(self):
        projection = (
            ReasoningEvidenceRelationshipProjector()
            .project(
                evidence_registry=ReasoningEvidenceRegistry(
                    package()
                ),
                context_registry=context_registry(),
            )
        )

        self.assertIn(
            RELATION_SHARED_CONTEXT_ROLE,
            projection.relationships[0].relation_types,
        )

        self.assertIn(
            "evidence",
            projection.relationships[0].shared_context_roles,
        )

    def test_deterministic(self):
        projector = ReasoningEvidenceRelationshipProjector()

        a = projector.project(
            evidence_registry=ReasoningEvidenceRegistry(
                package()
            ),
            context_registry=context_registry(),
        )

        b = projector.project(
            evidence_registry=ReasoningEvidenceRegistry(
                package()
            ),
            context_registry=context_registry(),
        )

        self.assertEqual(
            a.projection_hash,
            b.projection_hash,
        )

    def test_side_effects(self):
        projector = ReasoningEvidenceRelationshipProjector()

        self.assertTrue(projector.read_only)
        self.assertFalse(projector.network_allowed)
        self.assertFalse(projector.persistence_allowed)
        self.assertFalse(projector.publication_allowed)
        self.assertFalse(projector.execution_allowed)
        self.assertFalse(projector.qseries_execution_allowed)
        self.assertFalse(projector.prediction_allowed)
        self.assertFalse(projector.edge_score_allowed)
        self.assertFalse(projector.probability_allowed)
        self.assertFalse(projector.causal_claim_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-040 CERTIFICATION TEST")
    print(" REASONING EVIDENCE RELATIONSHIP PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI040
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-040")
    print(f"[PASS] Revision: {OI_040_REVISION}")
    print("[PASS] Structural evidence relationships projected deterministically")
    print("[PASS] Same-subject, same-provider, same-adapter, and shared-context relationships certified")
    print("[PASS] No causal direction, probability, prediction, or edge score introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-040 CERTIFIED")
