import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_010_continuous_physical_opportunity_scanner
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


    def test_canary_unchanged(self):
        self.assertEqual(
            q.LIVE_CANARY_SOL,
            0.001
        )


    def test_full_size_envelope(self):
        for x in (
            0.001,
            0.005,
            0.05,
            0.1,
            0.18,
            0.28,
            0.5,
            0.9,
            1.4,
        ):
            self.assertIn(
                x,
                q.SIZE_SOL
            )


    def test_physical_route_only(self):
        s=inspect.getsource(
            q.evaluate_size
        )

        self.assertIn(
            "physical.physical_route_for_size",
            s
        )


    def test_continuous_refresh(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "refresh_live_universe_rows",
            s
        )

        self.assertIn(
            "[SCAN_CYCLE]",
            s
        )


    def test_legacy_profit_not_used(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "api_pump_route",
            s
        )

        self.assertNotIn(
            "expectedOutAmount",
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
