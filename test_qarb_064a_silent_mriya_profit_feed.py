import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064a_silent_mriya_profit_feed as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_silent(self):
  s=inspect.getsource(q.collect);self.assertIn("redirect_stdout",s);self.assertIn("mriya_internal_feed.log",inspect.getsource(q))
 def test_profit_handoff(self):self.assertIn("hot.hydrate",inspect.getsource(q.candidates))
if __name__=="__main__":unittest.main(verbosity=2)
