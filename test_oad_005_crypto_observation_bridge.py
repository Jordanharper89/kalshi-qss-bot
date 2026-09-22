from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    build_adapter_request,
    verify_certified_adapter,
)
from qseries_v2.observation_adapters.oad_005_crypto_observation_bridge import (
    OAD_005_REVISION,
    FrozenOICryptoObservationBridge,
    verify_crypto_observation_bridge,
)

NOW = datetime(
    2026,
    8,
    11,
    20,
    0,
    tzinfo=timezone.utc,
)


class TestOAD005(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_crypto_observation_bridge()
        )

    def test_contract(self):
        adapter = FrozenOICryptoObservationBridge()
        self.assertTrue(
            verify_certified_adapter(adapter)
        )

    def test_identity(self):
        adapter = FrozenOICryptoObservationBridge()
        self.assertEqual(
            adapter.descriptor.identity.provider_id,
            "coinbase",
        )

    def test_capabilities(self):
        adapter = FrozenOICryptoObservationBridge()
        self.assertEqual(
            adapter.descriptor.capabilities,
            (
                "market_snapshot",
                "spot_price",
            ),
        )

    def test_unsupported_fails_closed(self):
        adapter = FrozenOICryptoObservationBridge()
        request = build_adapter_request(
            request_id="request.1",
            subject_hint="BTC",
            capability="place_order",
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
    print(" OAD-005 CERTIFICATION TEST")
    print(" FROZEN OI CRYPTO OBSERVATION BRIDGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD005
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-005")
    print(f"[PASS] Revision: {OAD_005_REVISION}")
    print("[PASS] Frozen OI-005 crypto observation path bridged into OAD contract")
    print("[PASS] Spot-price and market-snapshot capabilities preserved")
    print("[PASS] Unsupported capabilities fail closed")
    print("[PASS] Execution and order placement remain disabled")
    print("[DONE] OAD-005 CERTIFIED")
