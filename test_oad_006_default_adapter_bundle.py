from __future__ import annotations

import unittest

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    OAD_006_REVISION,
    build_default_adapter_bundle,
    verify_default_adapter_bundle,
)


class TestOAD006(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_default_adapter_bundle()
        )

    def test_adapters(self):
        bundle = build_default_adapter_bundle()

        self.assertEqual(
            bundle.adapter_ids,
            (
                "adapter.crypto.observe.v1",
                "adapter.kalshi.observe.v1",
            ),
        )

    def test_providers(self):
        bundle = build_default_adapter_bundle()

        self.assertEqual(
            bundle.provider_ids,
            (
                "coinbase",
                "kalshi",
            ),
        )

    def test_capabilities(self):
        bundle = build_default_adapter_bundle()

        self.assertIn(
            "market_discovery",
            bundle.capability_union,
        )
        self.assertIn(
            "market_snapshot",
            bundle.capability_union,
        )
        self.assertIn(
            "spot_price",
            bundle.capability_union,
        )

    def test_side_effects(self):
        bundle = build_default_adapter_bundle()

        self.assertTrue(bundle.read_only)
        self.assertFalse(
            bundle.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-006 CERTIFICATION TEST")
    print(" CERTIFIED DEFAULT ADAPTER BUNDLE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD006
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-006")
    print(f"[PASS] Revision: {OAD_006_REVISION}")
    print("[PASS] Kalshi and crypto bridges assembled into one deterministic adapter registry")
    print("[PASS] Provider and capability coverage exposed through one read-only bundle")
    print("[PASS] Execution remains disabled across the complete default bundle")
    print("[DONE] OAD-006 CERTIFIED")
