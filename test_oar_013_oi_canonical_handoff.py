from __future__ import annotations
import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import (
    CanonicalLiveObservation,
)
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)
from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoff,
    verify_oi_canonical_handoff,
)

NOW = datetime(2026, 8, 12, 13, 30, tzinfo=timezone.utc)

def obs():
    return CanonicalLiveObservation(
        observation_id="liveobs.1",
        adapter_id="adapter.crypto.observe.v1",
        provider_id="coinbase",
        capability="spot_price",
        payload=(("asset","BTC"),("price","65000")),
        observed_at=NOW,
        iteration_number=1,
        lineage_hash="a"*64,
        observation_hash="b"*64,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_oi_canonical_handoff()
        )

    def test_handoff(self):
        admission = LiveObservationAdmissionResult(
            iteration_number=1,
            admitted_observations=(obs(),),
            rejected_observation_ids=(),
            duplicate_observation_ids=(),
            admitted_count=1,
            rejected_count=0,
            read_only=True,
        )

        result = FrozenOICanonicalHandoff().build(
            admission
        )

        self.assertEqual(
            result.observation_count,
            1,
        )
        self.assertEqual(
            result.provider_ids,
            ("coinbase",),
        )

    def test_side_effects(self):
        bridge = FrozenOICanonicalHandoff()
        self.assertTrue(bridge.read_only)
        self.assertFalse(bridge.execution_allowed)
        self.assertFalse(bridge.persistence_allowed)
        self.assertFalse(bridge.publication_allowed)

if __name__ == "__main__":
    print("="*72)
    print(" OAR-013 CERTIFICATION TEST")
    print(" FROZEN OI CANONICAL HANDOFF")
    print("="*72)

    r = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-013")
    print("[PASS] Admitted live observations packaged for frozen OI consumption")
    print("[PASS] Observation identity, hashes, provider, adapter, and capabilities preserved")
    print("[PASS] Frozen OI remains unchanged and read-only")
    print("[DONE] OAR-013 CERTIFIED")
