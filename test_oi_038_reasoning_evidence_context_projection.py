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
    OI_038_REVISION,
    ReasoningEvidenceContextProjector,
    verify_reasoning_evidence_context_projection,
)

NOW = datetime(
    2026,
    8,
    11,
    3,
    0,
    tzinfo=timezone.utc,
)


def package():
    return OracleReasoningEvidencePackage(
        package_id="reasoning.astros",
        query_id="query.astros",
        profile_id="profile.market_explanation",
        subject_hint="Astros strikeouts",
        admission_status="admitted",
        admission_hash="a" * 64,
        materialization_hash="b" * 64,
        evidence_items=(
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.market",
                canonical_observation_hash="c" * 64,
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                observed_at=NOW,
            ),
            OracleReasoningEvidenceItem(
                canonical_observation_id="obs.lineup",
                canonical_observation_hash="d" * 64,
                adapter_id="adapter.sports.v1",
                provider="SportsFeed",
                subject="Astros",
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


class TestOI038(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_context_projection()
        )

    def test_projection(self):
        result = ReasoningEvidenceContextProjector().project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        self.assertEqual(
            result.context_count,
            2,
        )

    def test_market_role(self):
        result = ReasoningEvidenceContextProjector().project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        market = tuple(
            item
            for item in result.contexts
            if item.canonical_observation_id == "obs.market"
        )[0]

        self.assertIn(
            "market_state",
            market.context_roles,
        )

    def test_sports_role(self):
        result = ReasoningEvidenceContextProjector().project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        lineup = tuple(
            item
            for item in result.contexts
            if item.canonical_observation_id == "obs.lineup"
        )[0]

        self.assertIn(
            "sports_context",
            lineup.context_roles,
        )

    def test_deterministic(self):
        projector = ReasoningEvidenceContextProjector()

        a = projector.project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        b = projector.project(
            ReasoningEvidenceRegistry(
                package()
            )
        )

        self.assertEqual(
            a.projection_hash,
            b.projection_hash,
        )

    def test_side_effects(self):
        projector = ReasoningEvidenceContextProjector()

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
    print(" OI-038 CERTIFICATION TEST")
    print(" REASONING EVIDENCE CONTEXT PROJECTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI038
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-038")
    print(f"[PASS] Revision: {OI_038_REVISION}")
    print("[PASS] Reasoning-ready evidence projected into deterministic structural context roles")
    print("[PASS] Market-state, sports, event, environment, and source context remain generic")
    print("[PASS] Context projection introduces no causal claim, probability, prediction, or edge score")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-038 CERTIFIED")
