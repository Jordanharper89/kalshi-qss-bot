import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_011_adaptive_physical_breadth_scanner
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


    def test_canary(self):
        self.assertEqual(
            q.LIVE_CANARY_SOL,
            0.001
        )


    def test_anchor_coverage(self):
        for x in (
            0.001,
            0.01,
            0.05,
            0.18,
            0.5,
            1.4,
        ):
            self.assertIn(
                x,
                q.ANCHOR_SIZES
            )


    def test_full_envelope_preserved(self):
        self.assertGreater(
            len(
                q.FULL_SIZES
            ),
            len(
                q.ANCHOR_SIZES
            )
        )


    def test_physical_only(self):
        s=inspect.getsource(
            q.evaluate_sizes
        )

        self.assertIn(
            "q10.evaluate_size",
            s
        )


    def test_adaptive_refine(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[FAST_REJECT]",
            s
        )

        self.assertIn(
            "[REFINE]",
            s
        )


    def test_continuous_fresh_universe(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "refresh_live_universe_rows",
            s
        )


    def test_no_legacy_profit(self):
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

        self.assertNotIn(
            "HOT_SIGNAL",
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
