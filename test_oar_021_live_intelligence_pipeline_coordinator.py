from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import (
    CanonicalLiveObservation,
)
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)
from qseries_v2.observation_adapter_runtime.oar_021_live_intelligence_pipeline_coordinator import (
    LiveIntelligencePipelineCoordinator,
    verify_live_intelligence_pipeline_coordinator,
)

NOW = datetime(
    2026,
    8,
    12,
    14,
    0,
    tzinfo=timezone.utc,
)

def admission():
    observation = CanonicalLiveObservation(
        observation_id="liveobs.1",
        adapter_id="adapter.crypto.observe.v1",
        provider_id="coinbase",
        capability="spot_price",
        payload=(
            ("asset","BTC"),
            ("price","65000"),
        ),
        observed_at=NOW,
        iteration_number=1,
        lineage_hash="a"*64,
        observation_hash="b"*64,
        read_only=True,
    )

    return LiveObservationAdmissionResult(
        iteration_number=1,
        admitted_observations=(
            observation,
        ),
        rejected_observation_ids=(),
        duplicate_observation_ids=(),
        admitted_count=1,
        rejected_count=0,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_intelligence_pipeline_coordinator()
        )

    def test_coordinate(self):
        result = (
            LiveIntelligencePipelineCoordinator()
            .coordinate(
                admission()
            )
        )

        self.assertEqual(
            result.observation_count,
            1,
        )

        self.assertTrue(
            result.oi_ready
        )

        self.assertTrue(
            result.umd_ready
        )

        self.assertTrue(
            result.oml_ready
        )

        self.assertTrue(
            result.integration.lineage_valid
        )

    def test_side_effects(self):
        x = LiveIntelligencePipelineCoordinator()

        self.assertTrue(
            x.read_only
        )

        self.assertFalse(
            x.execution_allowed
        )

        self.assertFalse(
            x.persistence_allowed
        )

        self.assertFalse(
            x.publication_allowed
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-021 CERTIFICATION TEST")
    print(" LIVE INTELLIGENCE PIPELINE COORDINATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-021")
    print("[PASS] Admitted live observations coordinate through frozen OI, UMD request, and OML intake package")
    print("[PASS] OI/UMD/OML readiness and lineage preserved")
    print("[PASS] Persistence, publication, and execution remain disabled")
    print("[DONE] OAR-021 CERTIFIED")
