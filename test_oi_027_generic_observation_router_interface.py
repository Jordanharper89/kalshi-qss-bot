from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_013_observation_requirement_resolution import (
    ObservationRequirement,
    ObservationRequirementResolver,
    build_requirement_profile,
)
from qseries_v2.observation_intelligence.oi_027_generic_observation_router_interface import (
    OI_027_REVISION,
    GenericObservationNeed,
    GenericObservationRouterInterface,
    verify_generic_observation_router_interface,
)


def router():
    return GenericObservationRouterInterface(
        ObservationSourceRoutingRegistry(
            default_source_registry(),
            default_observation_route_rules(),
        )
    )


class TestOI027(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_generic_observation_router_interface()
        )

    def test_crypto_need(self):
        route = router().route_need(
            GenericObservationNeed(
                need_id="need.crypto.price",
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
                subject_hint="Bitcoin",
            )
        )

        self.assertEqual(
            route.route_decision.adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )

    def test_kalshi_market_need(self):
        route = router().route_need(
            GenericObservationNeed(
                need_id="need.sports.market",
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
                subject_hint="Astros strikeouts",
            )
        )

        self.assertEqual(
            route.route_decision.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_unavailable_adapter_fails_closed(self):
        route = router().route_need(
            GenericObservationNeed(
                need_id="need.sports.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                subject_hint="Astros",
            )
        )

        self.assertEqual(
            route.route_decision.adapter_ids,
            (),
        )

    def test_profile_routing(self):
        profile = build_requirement_profile(
            "profile.market_explanation",
            (
                ObservationRequirement(
                    requirement_id="requirement.market",
                    domain="sports",
                    entity_kind="market",
                    observation_type="market_snapshot",
                    required=True,
                    reason="current market state",
                ),
            ),
        )

        resolver = ObservationRequirementResolver(
            (profile,)
        )

        routes = router().route_profile(
            profile_id="profile.market_explanation",
            resolver=resolver,
            subject_hint="Astros strikeouts",
        )

        self.assertEqual(len(routes), 1)
        self.assertEqual(
            routes[0].route_decision.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_deterministic(self):
        interface = router()
        need = GenericObservationNeed(
            need_id="need.test",
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
            subject_hint="Bitcoin",
        )

        a = interface.route_need(need)
        b = interface.route_need(need)

        self.assertEqual(
            a.route_hash,
            b.route_hash,
        )

    def test_side_effects(self):
        interface = router()

        self.assertTrue(interface.read_only)
        self.assertFalse(interface.network_allowed)
        self.assertFalse(interface.persistence_allowed)
        self.assertFalse(interface.publication_allowed)
        self.assertFalse(interface.execution_allowed)
        self.assertFalse(interface.qseries_execution_allowed)
        self.assertFalse(interface.prediction_allowed)
        self.assertFalse(interface.edge_score_allowed)
        self.assertFalse(interface.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-027 CERTIFICATION TEST")
    print(" GENERIC OBSERVATION ROUTER INTERFACE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI027
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-027")
    print(f"[PASS] Revision: {OI_027_REVISION}")
    print("[PASS] Generic observation needs route through the certified adapter registry")
    print("[PASS] Requirement profiles route without category-specific reasoning code")
    print("[PASS] Missing adapter capabilities fail closed with empty routes")
    print("[PASS] Prediction, probability, edge scoring, publication, and execution disabled")
    print("[DONE] OI-027 CERTIFIED")
