import inspect
import unittest

from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20

class DummyLane:
    def __init__(self):
        self.rows=[]
    def submit(self,*args):
        self.rows.append(args)

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q20.EXECUTION_AUTHORITY)
        self.assertTrue(q20.PAPER_ONLY)
        self.assertFalse(q20.REAL_MONEY_MOVED)

    def test_latest_state_contract(self):
        lane=q20.LatestStateLane()
        lane.submit("T",{"x":1},1,1)
        lane.submit("T",{"x":2},2,2)
        self.assertEqual(lane.submitted,2)
        self.assertEqual(lane.replaced,1)
        self.assertEqual(lane.latest["T"][0]["x"],2)

    def test_stale_gate(self):
        self.assertEqual(q20.MAX_START_AGE_MS,750.0)

    def test_event_thread_does_not_price(self):
        s=inspect.getsource(q20._patched_process_event)
        self.assertIn("apply_account_event",s)
        self.assertIn("_lane.submit",s)
        self.assertNotIn("exact_snapshot_opportunities",s)

    def test_worker_is_exact(self):
        s=inspect.getsource(q20.LatestStateLane._price)
        self.assertIn("exact_snapshot_opportunities",s)
        self.assertIn("newer_waiting",s)

    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q20)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)
        self.assertNotIn("sendTransaction",s)

    def test_sizes(self):
        self.assertEqual(q20.FAST_SIZES,(0.001,0.010,0.050))
        self.assertEqual(q20.EXPAND_SIZES,(0.180,0.500,1.400))

if __name__=="__main__":
    unittest.main(verbosity=2)
