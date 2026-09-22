from __future__ import annotations
import unittest

from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)
from qseries_v2.observation_adapter_runtime.oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationHandoff,
)
from qseries_v2.observation_adapter_runtime.oar_015_oml_memory_intake_handoff import (
    OMLMemoryIntakeHandoff,
    verify_oml_memory_intake_handoff,
)

def oi():
    return FrozenOICanonicalHandoffRecord(
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

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oml_memory_intake_handoff()
        )

    def test_request(self):
        a=oi()
        u=UMDMarketCorrelationHandoff().build(a)
        r=OMLMemoryIntakeHandoff().build(
            oi_handoff=a,
            umd_request=u,
        )
        self.assertTrue(
            r.requires_market_identity_resolution
        )
        self.assertTrue(
            r.requires_evidence_lineage_preservation
        )

    def test_lineage_mismatch(self):
        a=oi()
        u=UMDMarketCorrelationHandoff().build(a)
        bad=type(u)(
            iteration_number=2,
            observation_ids=u.observation_ids,
            provider_ids=u.provider_ids,
            capability_ids=u.capability_ids,
            market_identity_required=True,
            related_market_resolution_required=True,
            read_only=True,
        )
        with self.assertRaises(ValueError):
            OMLMemoryIntakeHandoff().build(
                oi_handoff=a,
                umd_request=bad,
            )

if __name__=="__main__":
    print("="*72)
    print(" OAR-015 CERTIFICATION TEST")
    print(" OML MEMORY INTAKE HANDOFF")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-015")
    print("[PASS] Live observation identity and lineage packaged for frozen Oracle Memory intake")
    print("[PASS] UMD market-resolution dependency remains explicit")
    print("[PASS] OML boundary remains read-only; persistence is not enabled by OAR")
    print("[DONE] OAR-015 CERTIFIED")
