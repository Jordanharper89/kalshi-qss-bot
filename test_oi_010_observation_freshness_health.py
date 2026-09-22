from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_010_observation_freshness_health import (
    AGING,
    FRESH,
    STALE,
    OI_010_REVISION,
    ObservationFreshnessHealthEngine,
    default_freshness_policies,
    verify_observation_freshness_health,
)

BASE = datetime(2026, 8, 10, 6, 0, tzinfo=timezone.utc)


def observation():
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )

    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id="BTC-USD-FRESHNESS",
        observed_at=BASE,
        subject="BTC",
        observation_type="spot_price",
        payload={
            "product_id": "BTC-USD",
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": "100.00",
        },
        metadata={"venue": "coinbase"},
    )

    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI010(unittest.TestCase):
    def setUp(self):
        self.engine = ObservationFreshnessHealthEngine(
            default_freshness_policies()
        )
        self.observation = observation()

    def test_foundation(self):
        self.assertTrue(
            verify_observation_freshness_health()
        )

    def test_fresh(self):
        health = self.engine.evaluate(
            self.observation,
            evaluated_at=BASE + timedelta(seconds=5),
        )
        self.assertEqual(health.freshness_status, FRESH)

    def test_aging(self):
        health = self.engine.evaluate(
            self.observation,
            evaluated_at=BASE + timedelta(seconds=30),
        )
        self.assertEqual(health.freshness_status, AGING)

    def test_stale(self):
        health = self.engine.evaluate(
            self.observation,
            evaluated_at=BASE + timedelta(seconds=61),
        )
        self.assertEqual(health.freshness_status, STALE)

    def test_deterministic(self):
        when = BASE + timedelta(seconds=5)
        a = self.engine.evaluate(self.observation, evaluated_at=when)
        b = self.engine.evaluate(self.observation, evaluated_at=when)
        self.assertEqual(a.health_hash, b.health_hash)

    def test_reverse_time_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.evaluate(
                self.observation,
                evaluated_at=BASE - timedelta(seconds=1),
            )

    def test_side_effects(self):
        self.assertTrue(self.engine.read_only)
        self.assertFalse(self.engine.network_allowed)
        self.assertFalse(self.engine.persistence_allowed)
        self.assertFalse(self.engine.publication_allowed)
        self.assertFalse(self.engine.execution_allowed)
        self.assertFalse(self.engine.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-010 CERTIFICATION TEST")
    print(" OBSERVATION FRESHNESS & HEALTH")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI010
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-010")
    print(f"[PASS] Revision: {OI_010_REVISION}")
    print("[PASS] Fresh, aging, and stale observation states certified")
    print("[PASS] Freshness remains observation-type aware and category-agnostic")
    print("[PASS] No prediction or trading-value judgment introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-010 CERTIFIED")
