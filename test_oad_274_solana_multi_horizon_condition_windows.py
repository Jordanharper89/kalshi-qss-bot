import unittest

from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import (
    SolanaHistoricalObservation,
)
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import (
    _select_sampled_window,
    build_multi_horizon_solana_states,
)


def row(oid, ts, liq, buys, sells, vol, price):
    return SolanaHistoricalObservation(
        oid,
        "source.dex.solana.token_pools.X",
        "solana_token_pool_identity_liquidity",
        ts,
        None,
        "dexscreener",
        "X",
        {
            "token_address": "X",
            "pools": (
                {
                    "pair_address": "P",
                    "liquidity_usd": liq,
                    "buys_h24": buys,
                    "sells_h24": sells,
                    "volume_h24": vol,
                    "price_usd": price,
                },
            ),
        },
    )


class T(unittest.TestCase):
    def test_five_second_sampled_boundary_accepts_normal_overhead(self):
        rows = (
            row("a", "2026-09-01T00:00:00+00:00", 100, 10, 9, 100, 1.00),
            row("b", "2026-09-01T00:00:05.800000+00:00", 110, 12, 9, 120, 1.10),
        )

        selected = _select_sampled_window(rows, 5)
        self.assertEqual(tuple(x.observation_id for x in selected), ("a", "b"))

        states = build_multi_horizon_solana_states(rows, "X", (5,))
        self.assertEqual(len(states), 1)
        s = states[0]
        print("[5S] records=", s.records, "state=", s.state)
        print("[5S] first=", s.first_observed_at)
        print("[5S] last=", s.last_observed_at)
        self.assertEqual(s.records, 2)
        self.assertEqual(s.state, "WINDOW_READY")
        self.assertIsNone(s.probability)
        self.assertIsNone(s.direction)
        self.assertFalse(s.execution_authority)

    def test_stale_anchor_is_rejected(self):
        rows = (
            row("a", "2026-09-01T00:00:00+00:00", 100, 10, 9, 100, 1.00),
            row("b", "2026-09-01T00:00:20+00:00", 110, 12, 9, 120, 1.10),
        )

        selected = _select_sampled_window(rows, 5)
        print("[STALE] selected=", tuple(x.observation_id for x in selected))
        self.assertEqual(tuple(x.observation_id for x in selected), ("b",))

        states = build_multi_horizon_solana_states(rows, "X", (5,))
        self.assertEqual(states[0].state, "HOLD_TEMPORAL_DEPTH_REQUIRED")

    def test_existing_multi_horizon_contract_preserved(self):
        rows = (
            row("a", "2026-09-01T00:00:00+00:00", 100, 10, 9, 100, 1.00),
            row("b", "2026-09-01T00:00:05.800000+00:00", 110, 12, 9, 120, 1.10),
            row("c", "2026-09-01T00:00:15.600000+00:00", 130, 16, 10, 150, 1.20),
            row("d", "2026-09-01T00:00:30.500000+00:00", 150, 20, 11, 190, 1.30),
            row("e", "2026-09-01T00:01:00.700000+00:00", 175, 24, 12, 230, 1.40),
        )

        states = build_multi_horizon_solana_states(rows, "X", (5, 15, 30, 60))
        print("[WINDOWS]", tuple((x.window_seconds, x.records, x.state) for x in states))
        self.assertEqual(tuple(x.window_seconds for x in states), (5, 15, 30, 60))
        self.assertTrue(all(x.probability is None for x in states))
        self.assertTrue(all(x.direction is None for x in states))
        self.assertTrue(all(x.execution_authority is False for x in states))


if __name__ == "__main__":
    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-274 sampled-time horizon boundary rebuilt")
    print("[PASS] normal source/persistence overhead no longer defeats the 5-second window")
    print("[PASS] excessively stale boundary anchors remain HOLD")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
