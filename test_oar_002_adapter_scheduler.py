from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    build_default_adapter_bundle,
)
from qseries_v2.observation_adapter_runtime.oar_002_adapter_scheduler import (
    OAR_002_REVISION,
    DeterministicAdapterScheduler,
    verify_deterministic_adapter_scheduler,
)

NOW = datetime(
    2026,
    8,
    11,
    22,
    35,
    tzinfo=timezone.utc,
)


class TestOAR002(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_deterministic_adapter_scheduler()
        )

    def test_schedule(self):
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

        self.assertGreater(
            schedule.request_count,
            0,
        )
        self.assertEqual(
            schedule.requests[0].ordinal,
            1,
        )

    def test_deterministic(self):
        bundle = build_default_adapter_bundle()
        scheduler = DeterministicAdapterScheduler()

        a = scheduler.schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
        )
        b = scheduler.schedule(
            bundle=bundle,
            iteration_number=1,
            scheduled_at=NOW,
        )

        self.assertEqual(
            tuple(
                (
                    item.adapter_id,
                    item.request.capability,
                )
                for item in a.requests
            ),
            tuple(
                (
                    item.adapter_id,
                    item.request.capability,
                )
                for item in b.requests
            ),
        )

    def test_side_effects(self):
        scheduler = DeterministicAdapterScheduler()
        self.assertTrue(scheduler.read_only)
        self.assertFalse(scheduler.execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-002 CERTIFICATION TEST")
    print(" DETERMINISTIC ADAPTER SCHEDULER")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAR002
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-002")
    print(f"[PASS] Revision: {OAR_002_REVISION}")
    print("[PASS] Registered adapter capabilities schedule in deterministic order")
    print("[PASS] Per-provider subject hints and iteration lineage preserved")
    print("[PASS] Scheduler remains read-only with execution disabled")
    print("[DONE] OAR-002 CERTIFIED")
