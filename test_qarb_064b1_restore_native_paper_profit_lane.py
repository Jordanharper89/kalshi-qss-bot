import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064b_dynamic_profit_machine as q

class T(unittest.TestCase):

 def test_native_paper_lane_restored(self):
  s=inspect.getsource(q.serve)
  self.assertIn("qf.PaperSimulationLane",s)
  self.assertNotIn("FreshOnlyPaperLane",s)

 def test_dynamic_mriya_preserved(self):
  s=inspect.getsource(q.serve)
  self.assertIn("feed.collect",s)
  self.assertIn("_admit",s)

 def test_sixdex_preserved(self):
  s=inspect.getsource(q.serve)
  self.assertIn("q60b2.prepare_once",s)
  self.assertIn("q61d.capped_valves",s)

 def test_read_only(self):
  self.assertTrue(q.PAPER_ONLY)
  self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":
 unittest.main(verbosity=2)
