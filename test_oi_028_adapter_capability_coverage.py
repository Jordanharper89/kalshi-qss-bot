from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_008_observation_source_routing import (
    ObservationSourceRoutingRegistry,
    default_observation_route_rules,
)
from qseries_v2.observation_intelligence.oi_027_generic_observation_router_interface import (
    GenericObservationNeed,
    GenericObservationRouterInterface,
)
from qseries_v2.observation_intelligence.oi_028_adapter_capability_coverage import (
    OI_028_REVISION,
    AdapterCapabilityCoverageRegistry,
    verify_adapter_capability_coverage,
)


def coverage():
    registry = default_source_registry()

    router = GenericObservationRouterInterface(
        ObservationSourceRoutingRegistry(
            registry,
            default_observation_route_rules(),
        )
    )

    return AdapterCapabilityCoverageRegistry(
        adapter_registry=registry,
        router=router,
    )


class TestOI028(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_adapter_capability_coverage()
        )

    def test_covered_need(self):
        record = coverage().evaluate_need(
            GenericObservationNeed(
                need_id="need.crypto.price",
                domain="crypto",
                entity_kind="asset",
                observation_type="spot_price",
                subject_hint="Bitcoin",
            )
        )

        self.assertTrue(record.covered)
        self.assertEqual(
            record.adapter_ids,
            ("adapter.coinbase.spot.v1",),
        )

    def test_missing_need(self):
        record = coverage().evaluate_need(
            GenericObservationNeed(
                need_id="need.sports.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                subject_hint="Astros",
            )
        )

        self.assertFalse(record.covered)
        self.assertEqual(record.adapter_ids, ())

    def test_summary(self):
        summary = coverage().coverage_summary(
            (
                GenericObservationNeed(
                    need_id="need.a",
                    domain="crypto",
                    entity_kind="asset",
                    observation_type="spot_price",
                    subject_hint="Bitcoin",
                ),
                GenericObservationNeed(
                    need_id="need.b",
                    domain="sports",
                    entity_kind="team",
                    observation_type="lineup",
                    subject_hint="Astros",
                ),
            )
        )

        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["covered"], 1)
        self.assertEqual(summary["missing"], 1)

    def test_deterministic(self):
        need = GenericObservationNeed(
            need_id="need.crypto.price",
            domain="crypto",
            entity_kind="asset",
            observation_type="spot_price",
            subject_hint="Bitcoin",
        )

        a = coverage().evaluate_need(need)
        b = coverage().evaluate_need(need)

        self.assertEqual(
            a.coverage_hash,
            b.coverage_hash,
        )

    def test_side_effects(self):
        item = coverage()

        self.assertTrue(item.read_only)
        self.assertFalse(item.network_allowed)
        self.assertFalse(item.persistence_allowed)
        self.assertFalse(item.publication_allowed)
        self.assertFalse(item.execution_allowed)
        self.assertFalse(item.qseries_execution_allowed)
        self.assertFalse(item.prediction_allowed)
        self.assertFalse(item.edge_score_allowed)
        self.assertFalse(item.probability_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-028 CERTIFICATION TEST")
    print(" ADAPTER CAPABILITY COVERAGE REGISTRY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI028
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-028")
    print(f"[PASS] Revision: {OI_028_REVISION}")
    print("[PASS] Covered and missing observation needs certified against enabled adapters")
    print("[PASS] Adapter capability gaps are explicit and deterministic")
    print("[PASS] Missing capabilities fail closed without fallback guessing")
    print("[PASS] Prediction, probability, scoring, publication, and execution disabled")
    print("[DONE] OI-028 CERTIFIED")
