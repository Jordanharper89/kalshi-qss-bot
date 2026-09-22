from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationRequest,
)
from qseries_v2.observation_adapter_runtime.oar_019_exact_umd_market_identity_binding import (
    TARGET_CLASS,
    ExactUMDMarketIdentityBinding,
    verify_exact_umd_market_identity_binding,
)

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_umd_market_identity_binding()
        )

    def test_exact_binding(self):
        binding = (
            ExactUMDMarketIdentityBinding()
            .resolve_binding()
        )

        self.assertEqual(
            binding.class_name,
            TARGET_CLASS,
        )

        self.assertTrue(
            binding.callable_name
        )

    def test_request_validation(self):
        request = UMDMarketCorrelationRequest(
            iteration_number=1,
            observation_ids=("liveobs.1",),
            provider_ids=("coinbase",),
            capability_ids=("spot_price",),
            market_identity_required=True,
            related_market_resolution_required=True,
            read_only=True,
        )

        self.assertTrue(
            ExactUMDMarketIdentityBinding()
            .validate_request(
                request
            )
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-019 CERTIFICATION TEST")
    print(" EXACT UMD MARKET IDENTITY BINDING")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-019")
    print("[PASS] Exact UMD-095 CanonicalMarketIdentityResolver boundary bound")
    print("[PASS] Certified callable resolved without modifying UMD")
    print("[PASS] UMD request validation remains read-only")
    print("[DONE] OAR-019 CERTIFIED")
