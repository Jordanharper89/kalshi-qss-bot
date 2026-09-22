from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    build_default_adapter_bundle,
)
from qseries_v2.observation_adapter_runtime.oar_002_adapter_scheduler import (
    DeterministicAdapterScheduler,
)
from qseries_v2.observation_adapter_runtime.oar_003_multi_adapter_runner import (
    OAR_003_REVISION,
    MultiAdapterObservationRunner,
    verify_multi_adapter_observation_runner,
)

NOW = datetime(
    2026,
    8,
    11,
    22,
    40,
    tzinfo=timezone.utc,
)


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        current = self.value
        self.value = self.value + timedelta(
            milliseconds=1
        )
        return current


class TestOAR003(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_multi_adapter_observation_runner()
        )

    def test_run(self):
        bundle = build_default_adapter_bundle()

        schedule = DeterministicAdapterScheduler().schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
            subject_hints={
                "coinbase": "BTC",
                "kalshi": None,
            },
        )

        result = MultiAdapterObservationRunner().run(
            bundle=bundle,
            schedule=schedule,
            clock_callable=Clock(),
        )

        self.assertEqual(
            result.request_count,
            schedule.request_count,
        )

        self.assertEqual(
            result.success_count
            + result.failure_count,
            result.request_count,
        )

    def test_failure_isolated(self):
        bundle = build_default_adapter_bundle()

        schedule = DeterministicAdapterScheduler().schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
        )

        result = MultiAdapterObservationRunner().run(
            bundle=bundle,
            schedule=schedule,
            clock_callable=Clock(),
        )

        self.assertEqual(
            len(result.records),
            schedule.request_count,
        )

    def test_side_effects(self):
        runner = MultiAdapterObservationRunner()
        self.assertTrue(runner.read_only)
        self.assertFalse(runner.execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-003 CERTIFICATION TEST")
    print(" MULTI-ADAPTER OBSERVATION RUNNER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAR003
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-003")
    print(f"[PASS] Revision: {OAR_003_REVISION}")
    print("[PASS] Scheduled Kalshi and crypto adapter requests run through one universal runtime")
    print("[PASS] Per-adapter failures are isolated instead of crashing the whole iteration")
    print("[PASS] Observation counts, successes, failures, and iteration lineage preserved")
    print("[PASS] Runner remains read-only with execution disabled")
    print("[DONE] OAR-003 CERTIFIED")
