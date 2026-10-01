import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a6_damm_graph_ready_live_adapter as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY); self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_freshness(self): self.assertEqual(q.MAX_AGE_MS,750.0)
if __name__=="__main__": unittest.main(verbosity=2)
