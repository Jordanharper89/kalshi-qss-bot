import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_014_venue_native_fast_lane
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


    def test_direct_ws_pavement(self):

        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "q61d.install",
            s
        )

        self.assertIn(
            "persistent.serve",
            s
        )


    def test_event_is_trigger(self):

        s=inspect.getsource(
            q.install_event_trigger
        )

        self.assertIn(
            "apply_account_event",
            s
        )

        self.assertIn(
            "physical_lane.submit",
            s
        )


    def test_mriya_not_event_gate(self):

        s=inspect.getsource(
            q.install_event_trigger
        )

        self.assertNotIn(
            "MRIYA",
            s
        )

        self.assertNotIn(
            "last_seen_epoch",
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


    def test_bidirectional_physical(self):

        s=inspect.getsource(
            q.PhysicalFastLane._point
        )

        self.assertIn(
            "bi.safe_forward",
            s
        )

        self.assertIn(
            "bi.evaluate_reverse",
            s
        )


    def test_fast_then_expand(self):

        self.assertEqual(
            q.FAST_SIZES,
            (
                0.001,
                0.010,
                0.050,
            )
        )

        self.assertEqual(
            q.EXPANSION_SIZES,
            (
                0.180,
                0.500,
                1.400,
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
