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


    def test_live_universe(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "q80.q45.classify",
            s
        )

        self.assertIn(
            "q80.select_rows",
            s
        )

        self.assertIn(
            "recyclable_proven_tokens",
            s
        )


    def test_old_fixture_retired(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "live_universe_rows",
            s
        )

        self.assertNotIn(
            "base.load_micro_rows",
            s
        )


    def test_physical_gate_preserved(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_strategy_preserved(self):
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


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
