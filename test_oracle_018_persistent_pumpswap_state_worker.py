import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_018_persistent_pumpswap_state_worker
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


    def test_persistent_process(self):

        s=inspect.getsource(
            q.PumpWorker
        )

        self.assertIn(
            "subprocess.Popen",
            s
        )

        self.assertNotIn(
            "subprocess.run",
            s
        )


    def test_reserve_override(self):

        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            '"baseReserve"',
            s
        )

        self.assertIn(
            '"quoteReserve"',
            s
        )


    def test_no_rpc_in_quote_loop(self):

        s=q.JS.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            s.count(
                "swapSolanaState("
            ),
            1
        )

        self.assertIn(
            'req.command==="QUOTE"',
            s
        )


    def test_exact_sdk_math(self):

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


    def test_parity_gate(self):

        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "RESERVE_OVERRIDE_BASE_OUT_MISMATCH",
            s
        )

        self.assertIn(
            "RESERVE_OVERRIDE_MAX_QUOTE_MISMATCH",
            s
        )


    def test_no_private_key(self):

        s=q.Path(
            q.__file__
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "QSB_SOLANA_PRIVATE_KEY",
            s
        )


    def test_no_broadcast(self):

        s=q.Path(
            q.__file__
        ).read_text(
            encoding="utf-8"
        )

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
