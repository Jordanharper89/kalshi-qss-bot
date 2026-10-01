import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_071_continuous_mriya_replenishment as q
class T(unittest.TestCase):
 def test_exact_source(self):self.assertEqual(q.hot.__name__.split(".")[-1],"qarb_038b_nonrecursive_mriya_hotset_runtime")
 def test_policy(self):
  s=open(q.__file__,encoding="utf-8").read();self.assertIn('"sticky":True',s);self.assertIn("if t not in merged",s)
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
