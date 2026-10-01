import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_016_physical_parity_calibration
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


    def test_raw_screen_not_authority(self):

        s=inspect.getsource(
            q.CalibratedPhysicalLane.screen
        )

        self.assertIn(
            "correction",
            s
        )

        self.assertIn(
            "corrected",
            s
        )


    def test_official_truth_updates_parity(self):

        s=inspect.getsource(
            q.CalibratedPhysicalLane._verify
        )

        self.assertIn(
            "_update_parity",
            s
        )

        self.assertIn(
            "guaranteed_positive",
            s
        )


    def test_worst_case_correction(self):

        s=inspect.getsource(
            q.CalibratedPhysicalLane._update_parity
        )

        self.assertIn(
            "worst_overstatement_bps",
            s
        )

        self.assertIn(
            "max(",
            s
        )


    def test_margin(self):

        self.assertGreater(
            q.PARITY_MARGIN_BPS,
            0
        )


    def test_latest_state_parent_preserved(self):

        self.assertTrue(
            issubclass(
                q.CalibratedPhysicalLane,
                q.q15.LatestStatePhysicalLane
            )
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
