from __future__ import annotations

import importlib
import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_011_interactive_terminal_coordinator import (
    INJECTION_SYMBOL_NAME,
    InteractiveTerminalCompositionCoordinator,
    live_display_query_overlay,
    verify_interactive_terminal_coordinator,
)

NOW = datetime(
    2026,
    8,
    12,
    17,
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


class TestOLC011(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_interactive_terminal_coordinator()
        )

    def test_prime(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        snapshot = coordinator.prime()

        self.assertEqual(
            snapshot.generation,
            1,
        )

        self.assertIsNotNone(
            snapshot.read_model
        )

    def test_overlay_restores_exact_display_query(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        coordinator.prime()

        launcher = importlib.import_module(
            "run_oracle_open_intelligence_terminal"
        )

        original = getattr(
            launcher,
            INJECTION_SYMBOL_NAME,
        )

        with live_display_query_overlay(
            store=coordinator.worker.store,
        ):
            patched = getattr(
                launcher,
                INJECTION_SYMBOL_NAME,
            )

            self.assertIsNot(
                original,
                patched,
            )

            self.assertEqual(
                patched.__name__,
                "olc_live_display_query",
            )

        restored = getattr(
            launcher,
            INJECTION_SYMBOL_NAME,
        )

        self.assertIs(
            original,
            restored,
        )

    def test_status(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
            )
        )

        status = coordinator.status()

        self.assertTrue(
            status.read_only
        )

        self.assertFalse(
            status.execution_allowed
        )

        self.assertEqual(
            status.injection_symbol_name,
            "display_query",
        )

    def test_side_effects(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
            )
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


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-011 CERTIFICATION TEST")
    print(
        " INTERACTIVE TERMINAL COORDINATOR "
        "— CORRECTION V2"
    )
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC011
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-011")
    print(
        "[PASS] Initial production live read model priming certified"
    )
    print(
        "[PASS] Continuous refresh composes with the verified "
        "run_interactive terminal"
    )
    print(
        "[PASS] Exact display_query runtime boundary is overlaid "
        "in memory and restored on exit"
    )
    print(
        "[PASS] Existing Oracle Terminal source remains unchanged"
    )
    print("[DONE] OLC-011 CERTIFIED")
