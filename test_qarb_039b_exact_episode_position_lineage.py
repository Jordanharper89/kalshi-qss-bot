import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_039b_exact_episode_position_lineage as q
class T(unittest.TestCase):
    def test_busy_guard(self):
        s=inspect.getsource(q.ExactEpisodeLane.submit)
        self.assertIn("if k in self.busy",s);self.assertIn("return None",s)
    def test_release_only_at_90(self):
        s=inspect.getsource(q.ExactEpisodeLane.capture)
        self.assertIn('>=90.0',s);self.assertIn("self.busy.pop",s)
    def test_read_only(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
