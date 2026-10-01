import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q
class T(unittest.TestCase):
    def test_mode(self):
        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_existing_runner_preserved(self):
        src=inspect.getsource(q.q60b.p.serve)
        self.assertIn("state=m.prepare(root)",src.replace(" ",""))
    def test_single_hydration_source(self):
        src=inspect.getsource(q.main)
        self.assertIn("state,cap=prepare_once(root)",src.replace(" ",""))
        self.assertIn("q60b.m.prepare=cached_prepare",src.replace(" ",""))
    def test_no_execution(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":
    unittest.main(verbosity=2)
