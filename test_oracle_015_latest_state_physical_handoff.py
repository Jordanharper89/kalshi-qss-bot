import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_015_latest_state_physical_handoff
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


    def test_no_fifo_queue(self):

        s=inspect.getsource(
            q.LatestStatePhysicalLane
        )

        self.assertIn(
            "self.latest={}",
            s
        )

        self.assertNotIn(
            "queue.Queue",
            s
        )


    def test_newer_replaces_older(self):

        s=inspect.getsource(
            q.LatestStatePhysicalLane.screen
        )

        self.assertIn(
            "self.latest",
            s
        )

        self.assertIn(
            "self.coalesced",
            s
        )


    def test_inmemory_screen(self):

        s=inspect.getsource(
            q.LatestStatePhysicalLane.screen
        )

        self.assertIn(
            "evaluate_token",
            s
        )

        self.assertNotIn(
            "safe_forward",
            s
        )

        self.assertNotIn(
            "evaluate_reverse",
            s
        )


    def test_official_exact_point_only(self):

        s=inspect.getsource(
            q.LatestStatePhysicalLane._verify
        )

        self.assertIn(
            "bi.safe_forward",
            s
        )

        self.assertIn(
            "bi.evaluate_reverse",
            s
        )

        self.assertNotIn(
            "for size in",
            s
        )


    def test_stale_start_rejected(self):

        s=inspect.getsource(
            q.LatestStatePhysicalLane._verify
        )

        self.assertIn(
            "VERIFY_START_MAX_AGE_MS",
            s
        )

        self.assertIn(
            "VERIFY_STALE_DROP",
            s
        )


    def test_direct_event_screen(self):

        s=inspect.getsource(
            q.install_event_trigger
        )

        self.assertIn(
            "lane.screen",
            s
        )

        self.assertIn(
            "apply_account_event",
            s
        )


    def test_old_hot_signal_disabled(self):

        s=inspect.getsource(
            q.install_event_trigger
        )

        self.assertIn(
            "persistent._initial_scan",
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
