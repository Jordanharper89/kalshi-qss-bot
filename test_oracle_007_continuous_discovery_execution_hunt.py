import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )


    def test_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_continuous_discovery(self):
        self.assertTrue(
            callable(
                q._ensure_oracle_discovery
            )
        )

        self.assertTrue(
            callable(
                q.refresh_live_universe_rows
            )
        )


    def test_discovery_cleanup(self):
        self.assertTrue(
            callable(
                q._stop_oracle_discovery
            )
        )


    def test_stale_memory_not_execution(self):
        s=inspect.getsource(
            q.refresh_live_universe_rows
        )

        self.assertNotIn(
            "q80.select_rows",
            s
        )

        self.assertNotIn(
            "q80.MEMORY",
            s
        )


    def test_hot_only(self):
        s=inspect.getsource(
            q.refresh_live_universe_rows
        )

        self.assertIn(
            "age>hot_seconds",
            s
        )

        self.assertIn(
            "_oracle_hot_valid_until",
            s
        )


    def test_rolling_admission(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[ROLLING_ADMISSION]",
            s
        )

        self.assertIn(
            "refresh_live_universe_rows",
            s
        )

        self.assertIn(
            "row_map",
            s
        )


    def test_empty_set_does_not_end_hunt(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[HUNT_EMPTY]",
            s
        )


    def test_strategy_unchanged(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )

        self.assertIn(
            "meteora_swap",
            s
        )


    def test_signed_sim_required(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
