from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_036_oracle_reasoning_evidence_package import (
    OracleReasoningEvidenceItem,
    OracleReasoningEvidencePackage,
)
from qseries_v2.observation_intelligence.oi_037_reasoning_evidence_registry import (
    OI_037_REVISION,
    ReasoningEvidenceRegistry,
    verify_reasoning_evidence_registry,
)

NOW = datetime(
    2026,
    8,
    11,
    2,
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
                adapter_id="adapter.kalshi.v1",
                provider="Kalshi",
                subject="Astros strikeouts",
                observation_type="market_snapshot",
                observed_at=NOW,
            ),
        ),
        missing_need_count=0,
        built_at=NOW,
        package_hash="e" * 64,
        read_only=True,
        predictive=False,
    )


class TestOI037(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_reasoning_evidence_registry()
        )

    def test_registry(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            len(registry.records),
            2,
        )

    def test_get(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            registry.get("obs.1").adapter_id,
            "adapter.kalshi.v1",
        )

    def test_reverse_queries(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            len(
                registry.by_adapter(
                    "adapter.kalshi.v1"
                )
            ),
            2,
        )

        self.assertEqual(
            len(
                registry.by_subject(
                    "Astros strikeouts"
                )
            ),
            2,
        )

        self.assertEqual(
            len(
                registry.by_observation_type(
                    "market_snapshot"
                )
            ),
            2,
        )

    def test_unknown(self):
        registry = ReasoningEvidenceRegistry(
            package()
        )

        self.assertIsNone(
            registry.get("obs.unknown")
        )

        self.assertEqual(
            registry.by_provider("Unknown"),
            (),
        )

    def test_deterministic(self):
        a = ReasoningEvidenceRegistry(
            package()
        )

        b = ReasoningEvidenceRegistry(
            package()
        )

        self.assertEqual(
            a.registry_hash,
            b.registry_hash,
        )

    def test_side_effects(self):
        registry = ReasoningEvidenceRegistry(
            package()
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


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-037 CERTIFICATION TEST")
    print(" REASONING EVIDENCE REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI037
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-037")
    print(f"[PASS] Revision: {OI_037_REVISION}")
    print("[PASS] Reasoning-ready canonical evidence registry certified")
    print("[PASS] Evidence queries by identity, adapter, provider, subject, and observation type certified")
    print("[PASS] Registry remains deterministic, read-only, non-predictive, and non-scoring")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-037 CERTIFIED")
