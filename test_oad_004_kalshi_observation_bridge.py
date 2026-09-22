from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    build_adapter_request,
    verify_certified_adapter,
)
from qseries_v2.observation_adapters.oad_004_kalshi_observation_bridge import (
    OAD_004_REVISION,
    ADAPTER_ID,
    FrozenOIKalshiObservationBridge,
    verify_kalshi_observation_bridge,
)

NOW = datetime(
    2026,
    8,
    11,
    20,
    0,
    tzinfo=timezone.utc,
)


class TestOAD004(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_kalshi_observation_bridge()
        )

    def test_contract(self):
        adapter = FrozenOIKalshiObservationBridge()
        self.assertTrue(
            verify_certified_adapter(adapter)
        )

    def test_identity(self):
        adapter = FrozenOIKalshiObservationBridge()
        self.assertEqual(
            adapter.descriptor.identity.adapter_id,
            ADAPTER_ID,
        )
        self.assertEqual(
            adapter.descriptor.identity.provider_id,
            "kalshi",
        )

    def test_capabilities(self):
        adapter = FrozenOIKalshiObservationBridge()
        self.assertEqual(
            adapter.descriptor.capabilities,
            (
                "market_discovery",
                "market_snapshot",
            ),
        )

    def test_unsupported_fails_closed(self):
        adapter = FrozenOIKalshiObservationBridge()
        request = build_adapter_request(
            request_id="request.1",
            subject_hint="test",
            capability="trade",
            requested_at=NOW,
        )

        result = adapter.observe(request)

        self.assertFalse(result.success)
        self.assertEqual(
            result.error_code,
            "unsupported_capability",
        )
        self.assertFalse(
            result.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-004 CERTIFICATION TEST")
    print(" FROZEN OI KALSHI OBSERVATION BRIDGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD004
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-004")
    print(f"[PASS] Revision: {OAD_004_REVISION}")
    print("[PASS] Frozen OI-004 Kalshi observation path bridged into OAD contract")
    print("[PASS] Kalshi market discovery and snapshot capabilities preserved")
    print("[PASS] Unsupported capabilities fail closed")
    print("[PASS] Execution and order placement remain disabled")
    print("[DONE] OAD-004 CERTIFIED")
