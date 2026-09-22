from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.observation_intelligence.oi_005_public_market_data_adapter import (
    PublicMarketDataObservationAdapter,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_007_observation_history import (
    OI_007_REVISION,
    UniversalObservationHistory,
    verify_observation_history,
)


BASE = datetime(2026, 8, 10, 4, 0, tzinfo=timezone.utc)


def observation(index: int, price: str):
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )
    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id=f"BTC-USD-{index}",
        observed_at=BASE + timedelta(minutes=index),
        subject="BTC",
        observation_type="spot_price",
        payload={
            "product_id": "BTC-USD",
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": price,
        },
        metadata={"venue": "coinbase"},
    )
    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI007(unittest.TestCase):
    def setUp(self):
        self.a = observation(0, "100.0")
        self.b = observation(1, "101.0")
        self.history = UniversalObservationHistory((self.a, self.b))

    def test_foundation(self):
        self.assertTrue(verify_observation_history())

    def test_series(self):
        series = self.history.series(
            source_id="coinbase.public.spot",
            subject="btc",
            observation_type="spot_price",
        )
        self.assertEqual(series.observations, (self.a, self.b))

    def test_latest(self):
        self.assertIs(
            self.history.latest(
                source_id="coinbase.public.spot",
                subject="BTC",
                observation_type="spot_price",
            ),
            self.b,
        )

    def test_range(self):
        series = self.history.series(
            source_id="coinbase.public.spot",
            subject="BTC",
            observation_type="spot_price",
        )
        values = series.between(
            BASE,
            BASE + timedelta(seconds=30),
        )
        self.assertEqual(values, (self.a,))

    def test_deterministic(self):
        x = UniversalObservationHistory((self.a, self.b))
        y = UniversalObservationHistory((self.a, self.b))
        self.assertEqual(x.history_hash, y.history_hash)

    def test_unsorted_rejected(self):
        with self.assertRaises(ValueError):
            UniversalObservationHistory((self.b, self.a))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            UniversalObservationHistory((self.a, self.a))

    def test_side_effects(self):
        self.assertTrue(self.history.read_only)
        self.assertFalse(self.history.network_allowed)
        self.assertFalse(self.history.persistence_allowed)
        self.assertFalse(self.history.publication_allowed)
        self.assertFalse(self.history.execution_allowed)
        self.assertFalse(self.history.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-007 CERTIFICATION TEST")
    print(" UNIVERSAL OBSERVATION HISTORY FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI007
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-007")
    print(f"[PASS] Revision: {OI_007_REVISION}")
    print("[PASS] Canonical observation history series certified")
    print("[PASS] Latest and bounded temporal queries certified")
    print("[PASS] History remains source-agnostic and category-agnostic")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-007 CERTIFIED")
