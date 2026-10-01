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

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


    def test_two_directions(self):

        self.assertEqual(
            {
                q.PUMP_TO_METEORA,
                q.METEORA_TO_PUMP,
            },
            {
                "PUMP_TO_METEORA",
                "METEORA_TO_PUMP",
            }
        )


    def test_reverse_uses_official_meteora(self):

        s=inspect.getsource(
            q.reverse_meteora_buy
        )

        self.assertIn(
            "oracle003_meteora_swap.mjs",
            open(
                q.__file__,
                encoding="utf-8"
            ).read()
        )


    def test_reverse_uses_official_pump_sell(self):

        s=inspect.getsource(
            q.official_pump_sell
        )

        self.assertIn(
            "oracle012_pump_sell.mjs",
            open(
                q.__file__,
                encoding="utf-8"
            ).read()
        )


    def test_transfer_fee_accounting(self):

        s=inspect.getsource(
            q.evaluate_reverse
        )

        self.assertIn(
            "engine.net_received",
            s
        )


    def test_no_legacy_expected_out(self):

        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "expectedOutAmount",
            s
        )

        self.assertNotIn(
            "api_pump_route",
            s
        )


    def test_no_broadcast(self):

        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

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
