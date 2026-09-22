from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from qseries_v2.oracle_live_composition.olc_004_live_intelligence_cycle import (
    LiveIntelligenceCycleResult,
)
from qseries_v2.oracle_live_composition.olc_009_live_ask_registry_overlay import (
    LiveAskHandlerOverlay,
    verify_live_ask_registry_overlay,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    30,
    tzinfo=timezone.utc,
)


def cycle():
    read_model = TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.test",
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

    return LiveIntelligenceCycleResult(
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


class TestOLC009(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_ask_registry_overlay()
        )

    def test_live_intercept(self):
        store = AtomicLiveReadModelStore()
        store.publish(
            cycle()
        )

        called = []

        def fallback(query, *args, **kwargs):
            called.append(query)
            return "legacy"

        overlay = LiveAskHandlerOverlay(
            store=store,
            fallback_handler=fallback,
        )

        status, value = overlay.dispatch(
            "why is bitcoin moving?"
        )

        self.assertTrue(
            status.live_handled
        )

        self.assertFalse(
            status.fallback_used
        )

        self.assertEqual(
            status.observation_count,
            2,
        )

        self.assertEqual(
            called,
            [],
        )

    def test_legacy_fallback(self):
        store = AtomicLiveReadModelStore()

        def fallback(query, *args, **kwargs):
            return (
                "legacy",
                query,
            )

        overlay = LiveAskHandlerOverlay(
            store=store,
            fallback_handler=fallback,
        )

        status, value = overlay.dispatch(
            "show current session"
        )

        self.assertFalse(
            status.live_handled
        )

        self.assertTrue(
            status.fallback_used
        )

        self.assertEqual(
            value,
            (
                "legacy",
                "show current session",
            ),
        )

    def test_side_effects(self):
        store = AtomicLiveReadModelStore()

        overlay = LiveAskHandlerOverlay(
            store=store,
            fallback_handler=lambda query: query,
        )

        self.assertTrue(overlay.read_only)
        self.assertFalse(overlay.execution_allowed)
        self.assertFalse(overlay.source_mutation_allowed)
        self.assertFalse(overlay.publication_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-009 CERTIFICATION TEST")
    print(" LIVE /ASK COMMAND REGISTRY OVERLAY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC009
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-009")
    print("[PASS] Live /ask queries consume the latest atomic terminal read model")
    print("[PASS] Existing /ask handler remains an exact fallback when live handling is unavailable")
    print("[PASS] Overlay requires no Oracle Terminal source mutation")
    print("[DONE] OLC-009 CERTIFIED")
