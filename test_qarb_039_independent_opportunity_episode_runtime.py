import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_039_independent_opportunity_episode_runtime as q
class T(unittest.TestCase):
    def test_gap(self):self.assertEqual(q.EPISODE_GAP_SECONDS,2.0)
    def test_anchor_first(self):
        s=inspect.getsource(q.EpisodeLane.submit);self.assertIn('if ep["anchor"] is None',s)
    def test_original_runtime_not_rebuilt(self):
        s=inspect.getsource(q);self.assertNotIn("async def serve(",s);self.assertIn("hot.install()",s)
    def test_read_only(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
