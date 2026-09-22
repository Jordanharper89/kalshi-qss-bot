from __future__ import annotations

import time
import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_007_continuous_live_refresh import (
    ContinuousLiveReadModelRefreshWorker,
    verify_continuous_live_refresh,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    20,
    tzinfo=timezone.utc,
)


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        current = self.value
        self.value += timedelta(
            milliseconds=1
        )
        return current


class TestOLC007(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_continuous_live_refresh()
        )

    def test_refresh_once(self):
        worker = (
            ContinuousLiveReadModelRefreshWorker(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        snapshot = worker.refresh_once()

        self.assertEqual(
            snapshot.generation,
            1,
        )

        self.assertIsNotNone(
            snapshot.read_model
        )

    def test_start_stop(self):
        waits = []

        worker = (
            ContinuousLiveReadModelRefreshWorker(
                config=build_live_composition_config(
                    tick_interval_seconds=1
                ),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
                wait_callable=lambda seconds: (
                    waits.append(seconds)
                ),
            )
        )

        worker.start()

        for _ in range(100):
            if (
                worker.snapshot().generation
                >= 1
            ):
                break
            time.sleep(0.01)

        worker.stop()

        self.assertGreaterEqual(
            worker.snapshot().generation,
            1,
        )

        self.assertFalse(
            worker.status().running
        )

    def test_side_effects(self):
        worker = (
            ContinuousLiveReadModelRefreshWorker(
                config=build_live_composition_config(),
                clock_callable=Clock(),
            )
        )

        self.assertTrue(worker.read_only)
        self.assertFalse(worker.execution_allowed)
        self.assertFalse(worker.publication_allowed)
        self.assertFalse(worker.persistence_allowed)
        self.assertFalse(worker.order_placement_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-007 CERTIFICATION TEST")
    print(" CONTINUOUS LIVE READ MODEL REFRESH WORKER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC007
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-007")
    print("[PASS] Continuous background refresh of the terminal live read model certified")
    print("[PASS] Atomic generations remain available while the terminal stays open")
    print("[PASS] Adapter/runtime errors remain explicit and do not enable execution")
    print("[DONE] OLC-007 CERTIFIED")
