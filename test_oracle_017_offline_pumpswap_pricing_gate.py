import unittest
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_017_offline_pumpswap_pricing_gate
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


    def test_no_private_key(self):

        s=Path(
            q.__file__
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "QSB_SOLANA_PRIVATE_KEY",
            s
        )

        self.assertNotIn(
            "sendTransaction",
            s
        )


    def test_offline_helper_exists(self):

        self.assertTrue(
            q.JS.is_file()
        )


    def test_exact_sdk_exports(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "buyQuoteInput",
            s
        )

        self.assertIn(
            "sellBaseInput",
            s
        )

        self.assertIn(
            "OnlinePumpAmmSdk",
            s
        )


    def test_single_online_state_fetch(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            s.count(
                "swapSolanaState("
            ),
            1
        )


    def test_large_offline_loop(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "offlineIterations",
            s
        )

        self.assertIn(
            "p99Ms",
            s
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
