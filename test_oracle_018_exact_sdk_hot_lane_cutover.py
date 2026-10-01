import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_018_exact_sdk_hot_lane_cutover
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


    def test_exact_sdk_worker(self):

        s=q.WORKER_JS.read_text(
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


    def test_persistent_worker(self):

        s=inspect.getsource(
            q.PumpSdkWorker
        )

        self.assertIn(
            "subprocess.Popen",
            s
        )

        self.assertNotIn(
            "subprocess.run",
            s
        )


    def test_websocket_reserves_feed_sdk(self):

        s=inspect.getsource(
            q.PumpSdkWorker.buy
        )

        self.assertIn(
            "pump_base_reserve",
            s
        )

        self.assertIn(
            "pump_quote_reserve",
            s
        )


    def test_token2022_net_receipt(self):

        s=inspect.getsource(
            q.exact_snapshot_opportunities
        )

        self.assertIn(
            "token_net",
            s
        )


    def test_bidirectional(self):

        s=inspect.getsource(
            q.exact_snapshot_opportunities
        )

        self.assertIn(
            "METEORA_TO_PUMP",
            s
        )

        self.assertIn(
            "PUMP_TO_METEORA",
            s
        )


    def test_old_fee_formula_absent(self):

        s=inspect.getsource(
            q.exact_snapshot_opportunities
        )

        self.assertNotIn(
            "PUMP_FEE_BPS",
            s
        )

        self.assertNotIn(
            "10000-PUMP",
            s
        )


    def test_snapshot_seam_replaced(self):

        s=inspect.getsource(
            q.install_exact_hot_math
        )

        self.assertIn(
            "sized_snapshot_opportunities",
            s
        )


    def test_official_verifier_preserved(self):

        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "q15.run",
            s
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
