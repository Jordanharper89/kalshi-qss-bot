import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_067_recover_real_atomic_simulator as q
class T(unittest.TestCase):
 def test_live_binding(self):
  r,p=q.install()
  self.assertIs(r.q60b.p.SimulationLane,q.DualLane)
 def test_real_simulator(self):
  self.assertTrue(callable(q.atomic.simulate_signal))
 def test_bounded_call(self):
  s=inspect.getsource(q.DualLane.worker)
  self.assertIn("asyncio.to_thread",s)
  self.assertIn("timeout=15.0",s)
  self.assertIn("ATOMIC_CALL_BEGIN",s)
  self.assertIn("ATOMIC_CALL_RETURN",s)
  self.assertIn("ATOMIC_SIM_TIMEOUT",s)
 def test_safety(self):
  self.assertTrue(q.PAPER_ONLY)
  self.assertFalse(q.EXECUTION_AUTHORITY)
  self.assertFalse(q.REAL_MONEY_MOVED)
if __name__=="__main__": unittest.main(verbosity=2)
