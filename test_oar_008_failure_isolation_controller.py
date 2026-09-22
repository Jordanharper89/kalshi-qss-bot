from __future__ import annotations
import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_007_adapter_health_model import (
    AdapterHealthRecord,
    HEALTHY,
    DEGRADED,
    FAILED,
)
from qseries_v2.observation_adapter_runtime.oar_008_failure_isolation_controller import (
    AdapterFailureIsolationController,
    ACTION_CONTINUE,
    ACTION_ISOLATE,
    ACTION_BLOCK,
    verify_failure_isolation_controller,
)

NOW = datetime(2026,8,12,4,50,tzinfo=timezone.utc)

def health(adapter_id, status):
    return AdapterHealthRecord(
        adapter_id=adapter_id,
        request_count=1,
        success_count=1 if status != FAILED else 0,
        failure_count=0 if status == HEALTHY else 1,
        observation_count=1 if status != FAILED else 0,
        health_status=status,
        assessed_at=NOW,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_failure_isolation_controller()
        )

    def test_actions(self):
        decisions = AdapterFailureIsolationController().decide(
            (
                health("adapter.a", HEALTHY),
                health("adapter.b", DEGRADED),
                health("adapter.c", FAILED),
            )
        )

        self.assertEqual(
            tuple(x.action for x in decisions),
            (
                ACTION_CONTINUE,
                ACTION_ISOLATE,
                ACTION_BLOCK,
            ),
        )

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            AdapterFailureIsolationController().decide(
                (
                    health("adapter.a", HEALTHY),
                    health("adapter.a", FAILED),
                )
            )

    def test_side_effects(self):
        controller = AdapterFailureIsolationController()
        self.assertTrue(controller.read_only)
        self.assertFalse(controller.execution_allowed)

if __name__ == "__main__":
    print("="*72)
    print(" OAR-008 CERTIFICATION TEST")
    print(" ADAPTER FAILURE ISOLATION CONTROLLER")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-008")
    print("[PASS] Healthy, degraded, and failed adapters receive deterministic isolation decisions")
    print("[PASS] One failing adapter can be isolated without authorizing execution")
    print("[PASS] Duplicate adapter health fails closed")
    print("[DONE] OAR-008 CERTIFIED")
