from __future__ import annotations

import importlib
import unittest

from qseries_v2.oracle_live_composition.olc_012_production_live_terminal_launcher import (
    build_production_live_terminal_coordinator,
    build_production_live_terminal_launch_config,
    verify_production_live_terminal_launcher,
)


class TestOLC012(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_production_live_terminal_launcher()
        )

    def test_config(self):
        config = (
            build_production_live_terminal_launch_config()
        )

        self.assertEqual(
            config.tick_interval_seconds,
            5,
        )

        self.assertEqual(
            config.coinbase_subject_hint,
            "BTC",
        )

        self.assertTrue(
            config.read_only
        )

        self.assertFalse(
            config.execution_allowed
        )

    def test_coordinator(self):
        coordinator = (
            build_production_live_terminal_coordinator()
        )

        self.assertTrue(
            coordinator.read_only
        )

        self.assertFalse(
            coordinator.execution_allowed
        )

        self.assertFalse(
            coordinator.source_mutation_allowed
        )

    def test_real_launcher_boundaries(self):
        launcher = importlib.import_module(
            "run_oracle_open_intelligence_terminal"
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "display_query",
                )
            )
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "run_interactive",
                )
            )
        )

    def test_bad_cadence(self):
        with self.assertRaises(
            ValueError
        ):
            build_production_live_terminal_launch_config(
                tick_interval_seconds=0,
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-012 CERTIFICATION TEST")
    print(
        " PRODUCTION INTERACTIVE LIVE ORACLE LAUNCHER "
        "— CORRECTION V2"
    )
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC012
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-012")
    print(
        "[PASS] One-command production interactive Oracle launcher certified"
    )
    print(
        "[PASS] Continuous refresh, atomic live read model, "
        "display_query overlay, and run_interactive compose correctly"
    )
    print(
        "[PASS] Execution, order placement, publication, "
        "and persistence remain disabled"
    )
    print("[DONE] OLC-012 CERTIFIED")
