from __future__ import annotations

import unittest

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    STATE_IDLE,
    build_live_composition_config,
    initial_live_composition_state,
    verify_live_composition_foundation,
)


class TestOLC001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_composition_foundation()
        )

    def test_config(self):
        config = build_live_composition_config()

        self.assertEqual(
            config.tick_interval_seconds,
            5,
        )

        self.assertTrue(
            config.legacy_terminal_fallback
        )

        self.assertTrue(
            config.read_only
        )

        self.assertFalse(
            config.execution_allowed
        )

    def test_initial_state(self):
        config = build_live_composition_config()

        state = initial_live_composition_state(
            config
        )

        self.assertEqual(
            state.state,
            STATE_IDLE,
        )

        self.assertFalse(
            state.live_runtime_ready
        )

        self.assertFalse(
            state.terminal_ready
        )

    def test_fallback_required(self):
        with self.assertRaises(ValueError):
            build_live_composition_config(
                legacy_terminal_fallback=False,
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-001 CERTIFICATION TEST")
    print(" ORACLE LIVE COMPOSITION FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC001
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-001")
    print("[PASS] Production composition identity, runtime identity, terminal identity, and cadence certified")
    print("[PASS] Existing Oracle Terminal fallback is mandatory")
    print("[PASS] Execution, order placement, publication, and portfolio mutation disabled")
    print("[DONE] OLC-001 CERTIFIED")
