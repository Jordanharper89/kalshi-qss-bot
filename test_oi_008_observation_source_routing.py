from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    OI_008_REVISION,
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
    verify_observation_source_routing,
)


class TestOI008(unittest.TestCase):
    def setUp(self):
        self.router = ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )

    def test_foundation(self):
        self.assertTrue(verify_observation_source_routing())

    def test_crypto_route(self):
        decision = self.router.route(
            ObservationRouteRequest(
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
            )
        )
        self.assertEqual(
            decision.adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )

    def test_kalshi_universal_route(self):
        decision = self.router.route(
            ObservationRouteRequest(
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
            )
        )
        self.assertEqual(
            decision.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_unknown_route(self):
        decision = self.router.route(
            ObservationRouteRequest(
                domain="sports",
                entity_kind="player",
                observation_type="lineup",
            )
        )
        self.assertEqual(decision.adapter_ids, ())

    def test_deterministic(self):
        request = ObservationRouteRequest(
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
        )
        self.assertEqual(
            self.router.route(request).decision_hash,
            self.router.route(request).decision_hash,
        )

    def test_side_effects(self):
        self.assertTrue(self.router.read_only)
        self.assertFalse(self.router.network_allowed)
        self.assertFalse(self.router.persistence_allowed)
        self.assertFalse(self.router.publication_allowed)
        self.assertFalse(self.router.execution_allowed)
        self.assertFalse(self.router.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-008 CERTIFICATION TEST")
    print(" OBSERVATION SOURCE ROUTING REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI008
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-008")
    print(f"[PASS] Revision: {OI_008_REVISION}")
    print("[PASS] Domain/entity/type routing to registered adapters certified")
    print("[PASS] Universal Kalshi market route certified")
    print("[PASS] Missing routes fail closed without guessing")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-008 CERTIFIED")
