from __future__ import annotations
import unittest

from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)
from qseries_v2.observation_adapter_runtime.oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationHandoff,
    verify_umd_market_correlation_handoff,
)

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_umd_market_correlation_handoff()
        )

    def test_request(self):
        oi = FrozenOICanonicalHandoffRecord(
            iteration_number=1,
            observation_ids=("liveobs.1",),
            observation_hashes=("a"*64,),
            adapter_ids=("adapter.crypto.observe.v1",),
            provider_ids=("coinbase",),
            capability_ids=("spot_price",),
            observation_count=1,
            frozen_oi_target="frozen",
            read_only=True,
        )

        request = UMDMarketCorrelationHandoff().build(oi)

        self.assertTrue(
            request.market_identity_required
        )
        self.assertTrue(
            request.related_market_resolution_required
        )

    def test_side_effects(self):
        x=UMDMarketCorrelationHandoff()
        self.assertTrue(x.read_only)
        self.assertFalse(x.execution_allowed)
        self.assertFalse(x.persistence_allowed)
        self.assertFalse(x.publication_allowed)

if __name__=="__main__":
    print("="*72)
    print(" OAR-014 CERTIFICATION TEST")
    print(" UMD MARKET CORRELATION HANDOFF")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-014")
    print("[PASS] Frozen-OI live observations packaged for UMD market identity and related-market resolution")
    print("[PASS] UMD handoff remains read-only and non-mutating")
    print("[DONE] OAR-014 CERTIFIED")
