from __future__ import annotations

import unittest

from qseries_v2.observation_intelligence.oi_013_observation_requirement_resolution import (
    OI_013_REVISION,
    ObservationRequirement,
    ObservationRequirementResolver,
    build_requirement_profile,
    verify_observation_requirement_resolution,
)


def profile():
    return build_requirement_profile(
        "profile.market_explanation",
        (
            ObservationRequirement(
                requirement_id="requirement.market_snapshot",
                domain="sports",
                entity_kind="market",
                observation_type="market_snapshot",
                required=True,
                reason="current market state",
            ),
            ObservationRequirement(
                requirement_id="requirement.news",
                domain="sports",
                entity_kind="team",
                observation_type="news",
                required=False,
                reason="context source when adapter exists",
            ),
        ),
    )


class TestOI013(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_requirement_resolution()
        )

    def test_profile(self):
        item = profile()
        self.assertEqual(
            item.profile_id,
            "profile.market_explanation",
        )

    def test_required_requests(self):
        resolver = ObservationRequirementResolver(
            (profile(),)
        )

        requests = resolver.required_requests(
            "profile.market_explanation"
        )

        self.assertEqual(len(requests), 1)
        self.assertEqual(
            requests[0].observation_type,
            "market_snapshot",
        )

    def test_deterministic(self):
        self.assertEqual(
            profile().profile_hash,
            profile().profile_hash,
        )

    def test_unknown_profile(self):
        resolver = ObservationRequirementResolver(
            (profile(),)
        )

        with self.assertRaises(ValueError):
            resolver.required_requests("missing")

    def test_side_effects(self):
        resolver = ObservationRequirementResolver(
            (profile(),)
        )
        self.assertTrue(resolver.read_only)
        self.assertFalse(resolver.network_allowed)
        self.assertFalse(resolver.persistence_allowed)
        self.assertFalse(resolver.publication_allowed)
        self.assertFalse(resolver.execution_allowed)
        self.assertFalse(resolver.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-013 CERTIFICATION TEST")
    print(" OBSERVATION REQUIREMENT RESOLUTION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI013
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-013")
    print(f"[PASS] Revision: {OI_013_REVISION}")
    print("[PASS] Generic evidence requirements resolve to route requests")
    print("[PASS] Required versus optional observation needs preserved")
    print("[PASS] No category-specific reasoning or prediction introduced")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-013 CERTIFIED")
