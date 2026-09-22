from __future__ import annotations

import unittest

from qseries_v2.observation_adapters.oad_001_adapter_foundation import (
    OAD_001_REVISION,
    build_adapter_descriptor,
    verify_observation_adapter_foundation,
)


class TestOAD001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_observation_adapter_foundation()
        )

    def test_descriptor(self):
        value = build_adapter_descriptor(
            adapter_id="adapter.kalshi.observe.v1",
            provider_id="kalshi",
            source_domain="prediction_market",
            version="1",
            capabilities=(
                "market_snapshot",
                "market_discovery",
            ),
        )

        self.assertTrue(value.read_only)
        self.assertFalse(value.execution_allowed)
        self.assertFalse(value.order_placement_allowed)

    def test_capabilities_deterministic(self):
        value = build_adapter_descriptor(
            adapter_id="adapter.test.v1",
            provider_id="test",
            source_domain="test",
            version="1",
            capabilities=("b", "a", "a"),
        )

        self.assertEqual(
            value.capabilities,
            ("a", "b"),
        )

    def test_invalid_state(self):
        with self.assertRaises(ValueError):
            build_adapter_descriptor(
                adapter_id="adapter.test.v1",
                provider_id="test",
                source_domain="test",
                version="1",
                capabilities=("x",),
                state="trading",
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-001 CERTIFICATION TEST")
    print(" OBSERVATION ADAPTER FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD001
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-001")
    print(f"[PASS] Revision: {OAD_001_REVISION}")
    print("[PASS] Universal read-only adapter identity and descriptor contracts certified")
    print("[PASS] Capability identity, provider identity, domain identity, and state are deterministic")
    print("[PASS] Execution, order placement, funds movement, and portfolio mutation disabled")
    print("[DONE] OAD-001 CERTIFIED")
