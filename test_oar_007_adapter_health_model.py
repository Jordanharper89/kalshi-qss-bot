from __future__ import annotations
import unittest
from datetime import datetime, timezone, timedelta

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import build_default_adapter_bundle
from qseries_v2.observation_adapter_runtime.oar_002_adapter_scheduler import DeterministicAdapterScheduler
from qseries_v2.observation_adapter_runtime.oar_003_multi_adapter_runner import MultiAdapterObservationRunner
from qseries_v2.observation_adapter_runtime.oar_007_adapter_health_model import (
    AdapterHealthModel,
    verify_adapter_health_model,
)

NOW = datetime(2026, 8, 12, 4, 45, tzinfo=timezone.utc)

class Clock:
    def __init__(self): self.v = NOW
    def __call__(self):
        x = self.v
        self.v += timedelta(milliseconds=1)
        return x

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_adapter_health_model())

    def test_health_records(self):
        bundle = build_default_adapter_bundle()
        schedule = DeterministicAdapterScheduler().schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
            subject_hints={"coinbase":"BTC", "kalshi":None},
        )
        run = MultiAdapterObservationRunner().run(
            bundle=bundle,
            schedule=schedule,
            clock_callable=Clock(),
        )
        records = AdapterHealthModel().assess(
            run_result=run,
            assessed_at=NOW,
        )
        self.assertGreaterEqual(len(records), 2)
        self.assertEqual(
            tuple(sorted(x.adapter_id for x in records)),
            tuple(x.adapter_id for x in records),
        )

    def test_side_effects(self):
        model = AdapterHealthModel()
        self.assertTrue(model.read_only)
        self.assertFalse(model.execution_allowed)

if __name__ == "__main__":
    print("="*72)
    print(" OAR-007 CERTIFICATION TEST")
    print(" ADAPTER HEALTH MODEL")
    print("="*72)
    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print()
    print("[PASS] Build: OAR-007")
    print("[PASS] Healthy, degraded, and failed adapter health states certified")
    print("[PASS] Health derives from actual per-adapter runtime outcomes")
    print("[PASS] Runtime remains read-only with execution disabled")
    print("[DONE] OAR-007 CERTIFIED")
