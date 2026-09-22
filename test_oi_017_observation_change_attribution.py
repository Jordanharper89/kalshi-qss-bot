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
from qseries_v2.observation_intelligence.oi_017_observation_change_attribution import (
    OI_017_REVISION,
    ObservationChangeAttributionEngine,
    verify_observation_change_attribution,
)

BASE = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def observation(index: int, price: str):
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )

    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id=f"BTC-{index}",
        observed_at=BASE + timedelta(minutes=index),
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
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI017(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_change_attribution()
        )

    def test_up(self):
        change = ObservationChangeAttributionEngine().compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "105"),
            value_field="price",
        )
        self.assertEqual(change.direction, "up")
        self.assertEqual(change.absolute_change, 5.0)

    def test_down(self):
        change = ObservationChangeAttributionEngine().compare_numeric(
            prior=observation(0, "105"),
            current=observation(1, "100"),
            value_field="price",
        )
        self.assertEqual(change.direction, "down")

    def test_unchanged(self):
        change = ObservationChangeAttributionEngine().compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "100"),
            value_field="price",
        )
        self.assertEqual(change.direction, "unchanged")

    def test_reverse_time_rejected(self):
        with self.assertRaises(ValueError):
            ObservationChangeAttributionEngine().compare_numeric(
                prior=observation(1, "100"),
                current=observation(0, "101"),
                value_field="price",
            )

    def test_deterministic(self):
        engine = ObservationChangeAttributionEngine()
        a = engine.compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "105"),
            value_field="price",
        )
        b = engine.compare_numeric(
            prior=observation(0, "100"),
            current=observation(1, "105"),
            value_field="price",
        )
        self.assertEqual(a.change_hash, b.change_hash)

    def test_side_effects(self):
        engine = ObservationChangeAttributionEngine()
        self.assertTrue(engine.read_only)
        self.assertFalse(engine.network_allowed)
        self.assertFalse(engine.persistence_allowed)
        self.assertFalse(engine.publication_allowed)
        self.assertFalse(engine.execution_allowed)
        self.assertFalse(engine.qseries_execution_allowed)
        self.assertFalse(engine.causal_inference_allowed)
        self.assertFalse(engine.prediction_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-017 CERTIFICATION TEST")
    print(" OBSERVATION CHANGE ATTRIBUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI017
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-017")
    print(f"[PASS] Revision: {OI_017_REVISION}")
    print("[PASS] Numeric observation changes and direction certified")
    print("[PASS] Prior/current observation lineage preserved")
    print("[PASS] Change attribution is descriptive only; no causal inference introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-017 CERTIFIED")
