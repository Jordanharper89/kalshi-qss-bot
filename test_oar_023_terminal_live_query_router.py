from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_023_terminal_live_query_router import (
    ROUTE_EXISTING_TERMINAL,
    ROUTE_LIVE_DIRECTION,
    ROUTE_LIVE_EXPLANATION,
    ROUTE_LIVE_FACT,
    TerminalLiveQueryRouter,
    verify_terminal_live_query_router,
)

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_live_query_router()
        )

    def test_fact(self):
        result = TerminalLiveQueryRouter().route(
            "what is the current price of bitcoin?"
        )

        self.assertEqual(
            result.route,
            ROUTE_LIVE_FACT,
        )

        self.assertTrue(
            result.live_intelligence_required
        )

    def test_explanation(self):
        result = TerminalLiveQueryRouter().route(
            "explain why the edge for up on Astros strikeouts just went up"
        )

        self.assertEqual(
            result.route,
            ROUTE_LIVE_EXPLANATION,
        )

        self.assertTrue(
            result.explanation_required
        )

    def test_direction(self):
        result = TerminalLiveQueryRouter().route(
            "where is bitcoin moving in the next hour"
        )

        self.assertEqual(
            result.route,
            ROUTE_LIVE_DIRECTION,
        )

        self.assertTrue(
            result.directional_reasoning_required
        )

    def test_fallback(self):
        result = TerminalLiveQueryRouter().route(
            "show me the current session"
        )

        self.assertEqual(
            result.route,
            ROUTE_EXISTING_TERMINAL,
        )

        self.assertFalse(
            result.live_intelligence_required
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-023 CERTIFICATION TEST")
    print(" TERMINAL QUERY-TO-LIVE-INTELLIGENCE ROUTER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-023")
    print("[PASS] Live fact, explanation, and directional query routes certified")
    print("[PASS] Existing terminal fallback preserved for non-live queries")
    print("[PASS] Router remains generic across Kalshi categories and adapter domains")
    print("[DONE] OAR-023 CERTIFIED")
