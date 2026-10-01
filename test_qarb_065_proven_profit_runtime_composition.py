import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_065_proven_profit_runtime_composition as q

class T(unittest.TestCase):
 def test_no_new_serve(self):
  self.assertNotIn("async def serve(",inspect.getsource(q))

 def test_native_profit_lane(self):
  q.install()
  self.assertIs(q.p.SimulationLane,q.qf.PaperSimulationLane)

 def test_mriya_hotset_bound(self):
  q.install()
  self.assertIs(q.m.pd.prepare_pairs,q.silent_hot_prepare)

 def test_061d_is_runtime(self):
  self.assertIn("runtime.main(argv)",inspect.getsource(q.main))

 def test_mode(self):
  self.assertTrue(q.PAPER_ONLY)
  self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":
 unittest.main(verbosity=2)
