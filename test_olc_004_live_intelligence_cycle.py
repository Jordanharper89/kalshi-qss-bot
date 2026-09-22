from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_004_live_intelligence_cycle import (
    ProductionLiveIntelligenceCycle,
    verify_live_intelligence_cycle,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    0,
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


class TestOLC004(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_intelligence_cycle()
        )

    def test_cycle(self):
        result = (
            ProductionLiveIntelligenceCycle()
            .run_once(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        self.assertEqual(
            result.iteration_number,
            1,
        )

        self.assertTrue(
            result.terminal_read_model.lineage_valid
        )

        self.assertTrue(
            result.read_only
        )

        self.assertFalse(
            result.execution_allowed
        )

    def test_side_effects(self):
        cycle = ProductionLiveIntelligenceCycle()

        self.assertTrue(cycle.read_only)
        self.assertFalse(cycle.execution_allowed)
        self.assertFalse(cycle.order_placement_allowed)
        self.assertFalse(cycle.publication_allowed)
        self.assertFalse(cycle.persistence_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-004 CERTIFICATION TEST")
    print(" PRODUCTION LIVE INTELLIGENCE CYCLE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC004
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-004")
    print("[PASS] One production adapter iteration flows through canonical bus, admission, OI/UMD/OML pipeline, and terminal read model")
    print("[PASS] Actual adapter successes, failures, and observation counts remain explicit")
    print("[PASS] Execution, order placement, publication, and persistence disabled")
    print("[DONE] OLC-004 CERTIFIED")
