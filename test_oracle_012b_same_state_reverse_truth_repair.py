import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_012_bidirectional_physical_market_scanner
    as q
)


class T(unittest.TestCase):

    def test_safety(self):

        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )


    def test_single_state_pair_api(self):

        s=inspect.getsource(
            q.official_pump_sell_pair
        )

        self.assertIn(
            "baseAmounts",
            s
        )

        self.assertIn(
            "stateSnapshots",
            s
        )


    def test_old_double_call_retired(self):

        s=inspect.getsource(
            q.evaluate_reverse
        )

        self.assertNotIn(
            "official_pump_sell(",
            s
        )

        self.assertEqual(
            s.count(
                "official_pump_sell_pair("
            ),
            1
        )


    def test_monotonicity_guard(self):

        s=inspect.getsource(
            q.official_pump_sell_pair
        )

        self.assertIn(
            "PUMP_SELL_MONOTONICITY_VIOLATION",
            s
        )


    def test_reverse_end_guard(self):

        s=inspect.getsource(
            q.evaluate_reverse
        )

        self.assertIn(
            "REVERSE_END_MONOTONICITY_VIOLATION",
            s
        )


    def test_two_directions_preserved(self):

        self.assertEqual(
            q.PUMP_TO_METEORA,
            "PUMP_TO_METEORA"
        )

        self.assertEqual(
            q.METEORA_TO_PUMP,
            "METEORA_TO_PUMP"
        )


    def test_no_broadcast(self):

        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            s=f.read()

        self.assertNotIn(
            "sendTransaction",
            s
        )

        self.assertNotIn(
            "send_once(",
            s
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
