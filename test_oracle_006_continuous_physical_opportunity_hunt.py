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


    def test_hot_expiry(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "_oracle_hot_valid_until",
            s
        )

        self.assertIn(
            "hot_seconds-age",
            s
        )


    def test_continuous_hunt(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[HUNT_ROUND]",
            s
        )

        self.assertIn(
            "[HUNT_HOLD]",
            s
        )

        self.assertIn(
            "hunt_round",
            s
        )


    def test_no_one_shot_paper_hold(self):
        s=inspect.getsource(
            q.run
        )

        self.assertNotIn(
            "[PAPER_HOLD]",
            s
        )


    def test_strategy(self):
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


    def test_no_new_alt(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "createLookupTable",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
