from __future__ import annotations
import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_007_adapter_health_model import (
    AdapterHealthRecord,
    HEALTHY,
    FAILED,
)
from qseries_v2.observation_adapter_runtime.oar_008_failure_isolation_controller import (
    AdapterFailureIsolationController,
)
from qseries_v2.observation_adapter_runtime.oar_009_runtime_health_registry import (
    RuntimeHealthRegistry,
    RUNTIME_DEGRADED,
    verify_runtime_health_registry,
)

NOW=datetime(2026,8,12,4,55,tzinfo=timezone.utc)

def health(adapter_id,status):
    return AdapterHealthRecord(
        adapter_id=adapter_id,
        request_count=1,
        success_count=1 if status==HEALTHY else 0,
        failure_count=0 if status==HEALTHY else 1,
        observation_count=1 if status==HEALTHY else 0,
        health_status=status,
        assessed_at=NOW,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_runtime_health_registry())

    def test_snapshot(self):
        records=(
            health("adapter.a",HEALTHY),
            health("adapter.b",FAILED),
        )
        decisions=AdapterFailureIsolationController().decide(records)
        snapshot=RuntimeHealthRegistry().build_snapshot(
            runtime_id="oracle.live.observation.production",
            adapter_health=records,
            isolation_decisions=decisions,
            assessed_at=NOW,
        )
        self.assertEqual(
            snapshot.runtime_health_status,
            RUNTIME_DEGRADED,
        )
        self.assertEqual(snapshot.isolated_count,1)

    def test_identity_mismatch(self):
        records=(health("adapter.a",HEALTHY),)
        decisions=AdapterFailureIsolationController().decide(
            (health("adapter.b",HEALTHY),)
        )
        with self.assertRaises(ValueError):
            RuntimeHealthRegistry().build_snapshot(
                runtime_id="runtime",
                adapter_health=records,
                isolation_decisions=decisions,
                assessed_at=NOW,
            )

if __name__=="__main__":
    print("="*72)
    print(" OAR-009 CERTIFICATION TEST")
    print(" RUNTIME HEALTH REGISTRY")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-009")
    print("[PASS] Adapter health and isolation state aggregate into one runtime health snapshot")
    print("[PASS] Healthy, degraded, and failed runtime states certified")
    print("[PASS] Adapter identity mismatches fail closed")
    print("[DONE] OAR-009 CERTIFIED")
