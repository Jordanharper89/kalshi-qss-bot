from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.observation_adapter_runtime.oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
    verify_terminal_live_query_e2e,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    30,
    tzinfo=timezone.utc,
)


def read_model():
    return TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.1",
        iteration_number=1,
        observation_count=3,
        observation_ids=(
            "liveobs.1",
            "liveobs.2",
            "liveobs.3",
        ),
        provider_ids=(
            "coinbase",
            "kalshi",
        ),
        capability_ids=(
            "market_snapshot",
            "spot_price",
        ),
        oi_ready=True,
        umd_ready=True,
        oml_ready=True,
        lineage_valid=True,
        generated_at=NOW,
        evidence_hash="a"*64,
        read_only=True,
    )


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_live_query_e2e()
        )

    def test_bitcoin_explanation(self):
        result = (
            TerminalLiveQueryEndToEnd()
            .execute(
                query="why is bitcoin moving?",
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.live_handled
        )

        self.assertEqual(
            result.observation_count,
            3,
        )

        self.assertFalse(
            result.fallback_to_existing_terminal
        )

    def test_kalshi_explanation(self):
        result = (
            TerminalLiveQueryEndToEnd()
            .execute(
                query=(
                    "explain why the edge for up "
                    "on Astros strikeouts just went up"
                ),
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.live_handled
        )

        self.assertFalse(
            result.fallback_to_existing_terminal
        )

    def test_existing_terminal_fallback(self):
        result = (
            TerminalLiveQueryEndToEnd()
            .execute(
                query="show current session",
                read_model=read_model(),
            )
        )

        self.assertFalse(
            result.live_handled
        )

        self.assertTrue(
            result.fallback_to_existing_terminal
        )

    def test_side_effects(self):
        x = TerminalLiveQueryEndToEnd()

        self.assertTrue(
            x.read_only
        )

        self.assertFalse(
            x.execution_allowed
        )

        self.assertFalse(
            x.publication_allowed
        )

        self.assertFalse(
            x.persistence_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-027 CERTIFICATION TEST")
    print(" TERMINAL LIVE QUERY END-TO-END READ PATH")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-027")
    print("[PASS] Bitcoin live explanation query traverses the new read-only terminal path")
    print("[PASS] Kalshi category explanation query traverses the same generic live path")
    print("[PASS] Existing terminal fallback remains intact")
    print("[PASS] Execution, publication, and persistence remain disabled")
    print("[DONE] OAR-027 CERTIFIED")
