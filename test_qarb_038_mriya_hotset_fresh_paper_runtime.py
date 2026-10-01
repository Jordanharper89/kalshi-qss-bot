import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038_mriya_hotset_fresh_paper_runtime as q
class T(unittest.TestCase):
    def test_original_serve(self):
        s=inspect.getsource(q);self.assertNotIn("async def serve(",s);self.assertIn("runtime.serve(Path.cwd()",s)
    def test_priority_prepare(self):
        s=inspect.getsource(q.install);self.assertIn("p.m.pd.prepare_pairs=priority_prepare_pairs",s)
    def test_fresh_lane(self):
        s=inspect.getsource(q.install);self.assertIn("FreshOnlyPaperLane",s);self.assertIn("tracked_apply",s)
    def test_read_only(self):
        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
