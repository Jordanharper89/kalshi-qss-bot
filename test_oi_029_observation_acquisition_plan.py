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
    GenericObservationRouterInterface,
)
from qseries_v2.observation_intelligence.oi_028_adapter_capability_coverage import (
    AdapterCapabilityCoverageRegistry,
)
from qseries_v2.observation_intelligence.oi_029_observation_acquisition_plan import (
    OI_029_REVISION,
    ObservationAcquisitionPlanBuilder,
    verify_observation_acquisition_plan,
)


def builder():
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
            ObservationRequirement(
                requirement_id="requirement.lineup",
                domain="sports",
                entity_kind="team",
                observation_type="lineup",
                required=True,
                reason="team lineup context",
            ),
        ),
    )

    resolver = ObservationRequirementResolver(
        (profile,)
    )

    registry = default_source_registry()

    router = GenericObservationRouterInterface(
        ObservationSourceRoutingRegistry(
            registry,
            default_observation_route_rules(),
        )
    )

    coverage = AdapterCapabilityCoverageRegistry(
        adapter_registry=registry,
        router=router,
    )

    return ObservationAcquisitionPlanBuilder(
        resolver=resolver,
        coverage_registry=coverage,
    )


class TestOI029(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_acquisition_plan()
        )

    def test_plan(self):
        plan = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        self.assertEqual(len(plan.items), 2)
        self.assertEqual(plan.covered_count, 1)
        self.assertEqual(plan.missing_count, 1)
        self.assertFalse(plan.complete_coverage)

    def test_covered_adapter_preserved(self):
        plan = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        market_item = tuple(
            item
            for item in plan.items
            if item.observation_type == "market_snapshot"
        )[0]

        self.assertEqual(
            market_item.adapter_ids,
            ("adapter.kalshi.v1",),
        )

    def test_missing_adapter_explicit(self):
        plan = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        lineup_item = tuple(
            item
            for item in plan.items
            if item.observation_type == "lineup"
        )[0]

        self.assertFalse(lineup_item.covered)
        self.assertEqual(lineup_item.adapter_ids, ())

    def test_deterministic(self):
        a = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        b = builder().build(
            plan_id="plan.astros",
            profile_id="profile.market_explanation",
            subject_hint="Astros strikeouts",
        )

        self.assertEqual(a.plan_hash, b.plan_hash)

    def test_side_effects(self):
        item = builder()

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
    print(" OI-029 CERTIFICATION TEST")
    print(" OBSERVATION ACQUISITION PLAN")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI029
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-029")
    print(f"[PASS] Revision: {OI_029_REVISION}")
    print("[PASS] Requirement profiles convert into deterministic adapter acquisition plans")
    print("[PASS] Covered and missing observation needs remain explicit")
    print("[PASS] Missing adapter capability never silently downgrades a requirement")
    print("[PASS] Prediction, probability, scoring, publication, and execution disabled")
    print("[DONE] OI-029 CERTIFIED")
