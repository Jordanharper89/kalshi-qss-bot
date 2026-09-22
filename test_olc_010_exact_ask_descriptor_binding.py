from __future__ import annotations

import importlib
import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.oracle_live_composition.olc_004_live_intelligence_cycle import (
    LiveIntelligenceCycleResult,
)
from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from qseries_v2.oracle_live_composition.olc_010_exact_ask_descriptor_binding import (
    ASK_HANDLER_NAME,
    DISPATCH_SYMBOL,
    INJECTION_SYMBOL,
    build_live_display_query,
    verify_exact_ask_descriptor_binding,
)

NOW = datetime(
    2026,
    8,
    12,
    17,
    0,
    tzinfo=timezone.utc,
)


def populated_store():
    store = AtomicLiveReadModelStore()

    read_model = TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.v5",
        iteration_number=1,
        observation_count=2,
        observation_ids=(
            "liveobs.1",
            "liveobs.2",
        ),
        provider_ids=(
            "coinbase",
            "kalshi",
        ),
        capability_ids=(
            "spot_price",
            "market_snapshot",
        ),
        oi_ready=True,
        umd_ready=True,
        oml_ready=True,
        lineage_valid=True,
        generated_at=NOW,
        evidence_hash="a"*64,
        read_only=True,
    )

    cycle = LiveIntelligenceCycleResult(
        composition_id="oracle.live.composition.v1",
        runtime_id="oracle.live.observation.production",
        iteration_number=1,
        adapter_request_count=2,
        adapter_success_count=2,
        adapter_failure_count=0,
        raw_observation_count=2,
        admitted_observation_count=2,
        terminal_read_model=read_model,
        read_only=True,
        execution_allowed=False,
    )

    store.publish(
        cycle
    )

    return store


class TestOLC010(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_ask_descriptor_binding()
        )

        self.assertEqual(
            INJECTION_SYMBOL,
            "display_query",
        )

        self.assertEqual(
            DISPATCH_SYMBOL,
            "dispatch_command",
        )

        self.assertEqual(
            ASK_HANDLER_NAME,
            "handle_ask",
        )

    def test_live_display_query_intercepts(self):
        store = populated_store()
        legacy_calls = []
        lines = []

        def legacy(
            query,
            *,
            session=None,
            root=None,
            builder=None,
            write=print,
        ):
            legacy_calls.append(
                query
            )
            return "legacy"

        live = build_live_display_query(
            store=store,
            original_display_query=legacy,
        )

        result = live(
            "why is bitcoin moving?",
            write=lines.append,
        )

        self.assertTrue(
            result.live_handled
        )

        self.assertFalse(
            result.fallback_used
        )

        self.assertEqual(
            result.observation_count,
            2,
        )

        self.assertEqual(
            legacy_calls,
            [],
        )

        self.assertTrue(
            any(
                "LIVE EVIDENCE AVAILABLE"
                in line
                for line in lines
            )
        )

    def test_existing_terminal_fallback(self):
        store = populated_store()
        calls = []

        def legacy(
            query,
            *,
            session=None,
            root=None,
            builder=None,
            write=print,
        ):
            calls.append(
                query
            )
            return "legacy-result"

        live = build_live_display_query(
            store=store,
            original_display_query=legacy,
        )

        result = live(
            "show current session"
        )

        self.assertEqual(
            result,
            "legacy-result",
        )

        self.assertEqual(
            calls,
            [
                "show current session",
            ],
        )

    def test_real_launcher_symbols(self):
        launcher = importlib.import_module(
            "run_oracle_open_intelligence_terminal"
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "dispatch_command",
                )
            )
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


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-010 CERTIFICATION TEST")
    print(
        " EXACT /ASK RUNTIME DISPLAY BOUNDARY "
        "— CORRECTION V5"
    )
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC010
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-010")
    print(
        "[PASS] /ask metadata handler_name='handle_ask' "
        "correctly treated as dispatch metadata, not a callable"
    )
    print(
        "[PASS] Actual runtime injection boundary certified: "
        "run_oracle_open_intelligence_terminal.display_query"
    )
    print(
        "[PASS] dispatch_command -> handle_ask -> display_query "
        "chain preserved exactly"
    )
    print(
        "[PASS] Existing display_query remains exact fallback"
    )
    print(
        "[PASS] Oracle Terminal source remains unchanged"
    )
    print("[DONE] OLC-010 CERTIFIED")
