from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_003_live_runtime_terminal_composition import (
    LiveRuntimeTerminalCompositionPlanner,
    verify_live_runtime_terminal_composition,
)

MANIFEST = Path('C:\\Users\\jorda\\OneDrive\\Documents\\GitHub\\kalshi-qss-bot\\qseries_v2\\oracle_live_composition\\OLC_002_TERMINAL_RUNTIME_MANIFEST.json')


class TestOLC003(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_runtime_terminal_composition()
        )

    def test_plan(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        top = payload[
            "top_candidate"
        ]

        plan = (
            LiveRuntimeTerminalCompositionPlanner()
            .build(
                config=(
                    build_live_composition_config()
                ),
                terminal_module_name=(
                    top["module_name"]
                ),
                terminal_symbol_name=(
                    top["symbol_name"]
                ),
            )
        )

        self.assertTrue(
            plan.continuous_runtime_required
        )

        self.assertTrue(
            plan.live_read_model_required
        )

        self.assertTrue(
            plan.interactive_terminal_required
        )

        self.assertTrue(
            plan.legacy_terminal_fallback
        )

        self.assertEqual(
            plan.stages[-1],
            "enter_existing_interactive_oracle_terminal",
        )

    def test_side_effects(self):
        planner = (
            LiveRuntimeTerminalCompositionPlanner()
        )

        self.assertTrue(
            planner.read_only
        )

        self.assertFalse(
            planner.execution_allowed
        )

        self.assertFalse(
            planner.publication_allowed
        )

        self.assertFalse(
            planner.order_placement_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-003 CERTIFICATION TEST")
    print(" LIVE RUNTIME / TERMINAL COMPOSITION PLAN")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC003
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-003")
    print("[PASS] Live adapters, production observation runtime, canonical bus, OI/UMD/OML pipeline, terminal read model, and interactive terminal compose into one production plan")
    print("[PASS] Existing interactive Oracle Terminal remains the final command-loop boundary")
    print("[PASS] Execution, order placement, and publication remain disabled")
    print("[DONE] OLC-003 CERTIFIED")
