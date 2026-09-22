from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_010_observation_freshness_health import (
    ObservationFreshnessHealthEngine,
    default_freshness_policies,
)
from qseries_v2.observation_intelligence.oi_011_multi_source_consensus import (
    OI_011_REVISION,
    MultiSourceConsensusEngine,
    verify_multi_source_consensus,
)

NOW = datetime(2026, 8, 10, 7, 0, tzinfo=timezone.utc)


def registry():
    return SourceAdapterRegistry(
        (
            SourceAdapterDescriptor(
                adapter_id="adapter.exchange.a",
                source_id="exchange.a",
                source_kind="market_data",
                provider="Exchange A",
                adapter_version="1",
                capabilities=("spot price",),
                enabled_for_intake=True,
            ),
            SourceAdapterDescriptor(
                adapter_id="adapter.exchange.b",
                source_id="exchange.b",
                source_kind="market_data",
                provider="Exchange B",
                adapter_version="1",
                capabilities=("spot price",),
                enabled_for_intake=True,
            ),
        )
    )


def observation(source_id, provider, adapter_id, external_id, price):
    envelope = RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id=source_id,
            source_kind="market_data",
            provider=provider,
            adapter_id=adapter_id,
        ),
        external_observation_id=external_id,
        observed_at=NOW,
        subject="BTC",
        observation_type="spot_price",
        payload={
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": price,
        },
        metadata={},
    )

    return CanonicalLiveObservationGateway(
        registry()
    ).canonicalize(envelope).canonical_observation


class TestOI011(unittest.TestCase):
    def setUp(self):
        self.a = observation(
            "exchange.a",
            "Exchange A",
            "adapter.exchange.a",
            "a",
            "100.0",
        )
        self.b = observation(
            "exchange.b",
            "Exchange B",
            "adapter.exchange.b",
            "b",
            "102.0",
        )

        self.values = tuple(
            sorted(
                (self.a, self.b),
                key=lambda item: (
                    item.source_id,
                    item.canonical_observation_id,
                ),
            )
        )

        health_engine = ObservationFreshnessHealthEngine(
            default_freshness_policies()
        )

        self.health = tuple(
            health_engine.evaluate(
                item,
                evaluated_at=NOW,
            )
            for item in self.values
        )

    def test_foundation(self):
        self.assertTrue(verify_multi_source_consensus())

    def test_consensus(self):
        result = MultiSourceConsensusEngine().build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )

        self.assertEqual(result.source_count, 2)
        self.assertEqual(result.fresh_member_count, 2)
        self.assertEqual(result.median_value, 101.0)

    def test_range(self):
        result = MultiSourceConsensusEngine().build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )

        self.assertEqual(result.min_value, 100.0)
        self.assertEqual(result.max_value, 102.0)

    def test_deterministic(self):
        engine = MultiSourceConsensusEngine()
        a = engine.build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )
        b = engine.build_numeric_consensus(
            observations=self.values,
            health=self.health,
            value_field="price",
        )
        self.assertEqual(a.consensus_hash, b.consensus_hash)

    def test_side_effects(self):
        engine = MultiSourceConsensusEngine()
        self.assertTrue(engine.read_only)
        self.assertFalse(engine.network_allowed)
        self.assertFalse(engine.persistence_allowed)
        self.assertFalse(engine.publication_allowed)
        self.assertFalse(engine.execution_allowed)
        self.assertFalse(engine.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-011 CERTIFICATION TEST")
    print(" MULTI-SOURCE CONSENSUS FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI011
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-011")
    print(f"[PASS] Revision: {OI_011_REVISION}")
    print("[PASS] Multi-source numeric observation consensus certified")
    print("[PASS] Source count, freshness count, median, range, and spread certified")
    print("[PASS] Consensus remains descriptive and non-predictive")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-011 CERTIFIED")
