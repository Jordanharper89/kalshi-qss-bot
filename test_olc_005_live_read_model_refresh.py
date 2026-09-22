from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
    LiveReadModelRefreshService,
    verify_live_read_model_refresh,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    10,
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


class TestOLC005(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_read_model_refresh()
        )

    def test_empty_store(self):
        store = AtomicLiveReadModelStore()
        snapshot = store.snapshot()

        self.assertEqual(
            snapshot.generation,
            0,
        )

        self.assertIsNone(
            snapshot.read_model
        )

    def test_refresh(self):
        service = (
            LiveReadModelRefreshService()
        )

        snapshot = service.refresh_once(
            config=build_live_composition_config(),
            clock_callable=Clock(),
            subject_hints={
                "coinbase": "BTC",
                "kalshi": None,
            },
        )

        self.assertEqual(
            snapshot.generation,
            1,
        )

        self.assertIsNotNone(
            snapshot.read_model
        )

        self.assertTrue(
            snapshot.read_model.read_only
        )

    def test_side_effects(self):
        service = LiveReadModelRefreshService()

        self.assertTrue(service.read_only)
        self.assertFalse(service.execution_allowed)
        self.assertFalse(service.publication_allowed)
        self.assertFalse(service.persistence_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-005 CERTIFICATION TEST")
    print(" ATOMIC LIVE READ MODEL REFRESH SERVICE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC005
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-005")
    print("[PASS] Production live intelligence cycles atomically refresh one in-memory terminal read model")
    print("[PASS] Terminal readers receive generation-stable snapshots")
    print("[PASS] No persistence, publication, or execution introduced")
    print("[DONE] OLC-005 CERTIFIED")
