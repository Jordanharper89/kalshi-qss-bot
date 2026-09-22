from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_012_routed_observation_acquisition import (
    OI_012_REVISION,
    AdapterAcquisitionBinding,
    RoutedObservationAcquisitionEngine,
    verify_routed_observation_acquisition,
)

NOW = datetime(2026, 8, 10, 8, 0, tzinfo=timezone.utc)


def coinbase_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="coinbase.public.spot",
                source_kind="market_data",
                provider="Coinbase",
                adapter_id="adapter.coinbase.spot.v1",
            ),
            external_observation_id="BTC-USD-ROUTED",
            observed_at=NOW,
            subject="BTC",
            observation_type="spot_price",
            payload={
                "product_id": "BTC-USD",
                "symbol": "BTC",
                "quote_currency": "USD",
                "price": "100.0",
            },
            metadata={"venue": "coinbase"},
        ),
    )


def kalshi_acquire(request):
    return (
        RawObservationEnvelope(
            source=ObservationSourceIdentity(
                source_id="kalshi.public",
                source_kind="market_venue",
                provider="Kalshi",
                adapter_id="adapter.kalshi.v1",
            ),
            external_observation_id="KXTEST-ROUTED",
            observed_at=NOW,
            subject="Test Market",
            observation_type="market_snapshot",
            payload={
                "ticker": "KXTEST",
                "yes_bid": 50,
                "yes_ask": 52,
            },
            metadata={
                "venue": "kalshi",
                "market_ticker": "KXTEST",
            },
        ),
    )


class TestOI012(unittest.TestCase):
    def setUp(self):
        self.registry = default_source_registry()
        self.router = ObservationSourceRoutingRegistry(
            self.registry,
            default_observation_route_rules(),
        )
        self.engine = RoutedObservationAcquisitionEngine(
            adapter_registry=self.registry,
            routing_registry=self.router,
            bindings=(
                AdapterAcquisitionBinding(
                    adapter_id="adapter.coinbase.spot.v1",
                    acquire_callable=coinbase_acquire,
                ),
                AdapterAcquisitionBinding(
                    adapter_id="adapter.kalshi.v1",
                    acquire_callable=kalshi_acquire,
                ),
            ),
        )

    def test_foundation(self):
        self.assertTrue(
            verify_routed_observation_acquisition()
        )

    def test_crypto_acquisition(self):
        result = self.engine.acquire(
            query_id="query.crypto",
            request=ObservationRouteRequest(
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
            ),
            assembled_at=NOW,
        )

        self.assertEqual(
            result.invoked_adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(
            result.observations[0].subject,
            "BTC",
        )
        self.assertEqual(
            len(result.evidence_bundle.observations),
            1,
        )

    def test_kalshi_acquisition(self):
        result = self.engine.acquire(
            query_id="query.kalshi",
            request=ObservationRouteRequest(
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
            ),
            assembled_at=NOW,
        )

        self.assertEqual(
            result.invoked_adapter_ids,
            ("adapter.kalshi.v1",),
        )
        self.assertEqual(
            result.observations[0].metadata["market_ticker"],
            "KXTEST",
        )

    def test_unknown_route_fails_closed(self):
        result = self.engine.acquire(
            query_id="query.unknown",
            request=ObservationRouteRequest(
                domain="sports",
                entity_kind="player",
                observation_type="lineup",
            ),
            assembled_at=NOW,
        )

        self.assertEqual(result.invoked_adapter_ids, ())
        self.assertEqual(result.observations, ())
        self.assertEqual(result.evidence_bundle.observations, ())

    def test_deterministic(self):
        request = ObservationRouteRequest(
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
        )

        a = self.engine.acquire(
            query_id="query.crypto",
            request=request,
            assembled_at=NOW,
        )

        b = self.engine.acquire(
            query_id="query.crypto",
            request=request,
            assembled_at=NOW,
        )

        self.assertEqual(a.acquisition_hash, b.acquisition_hash)

    def test_side_effects(self):
        self.assertTrue(self.engine.read_only)
        self.assertFalse(self.engine.persistence_allowed)
        self.assertFalse(self.engine.publication_allowed)
        self.assertFalse(self.engine.execution_allowed)
        self.assertFalse(self.engine.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-012 CERTIFICATION TEST")
    print(" ROUTED OBSERVATION ACQUISITION ENGINE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI012
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-012")
    print(f"[PASS] Revision: {OI_012_REVISION}")
    print("[PASS] Route decisions invoke only registered adapter bindings")
    print("[PASS] Routed envelopes canonicalize through OI-003")
    print("[PASS] Routed observations assemble directly into immutable evidence bundles")
    print("[PASS] Missing adapter routes fail closed with empty evidence")
    print("[PASS] Persistence, publication, action authorization, and execution disabled")
    print("[DONE] OI-012 CERTIFIED")
