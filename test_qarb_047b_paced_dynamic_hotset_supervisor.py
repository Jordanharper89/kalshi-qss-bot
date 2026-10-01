import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_047b_paced_dynamic_hotset_supervisor as q
class T(unittest.TestCase):
    def test_uses_043b(self):
        s=inspect.getsource(q.supervisor);self.assertIn("run_qarb_043b_paced_mriya_token_discovery.py",s)
        self.assertNotIn("run_qarb_043_continuous_mriya_token_discovery.py",s)
    def test_uses_045b(self):self.assertIn("qarb_045b_evidence_window_hotset_lifecycle",inspect.getsource(q))
    def test_drain(self):self.assertIn("self.admit_seconds",inspect.getsource(q.AgeDrainLane.submit))
    def test_no_execution(self):self.assertFalse(q.EXECUTION_AUTHORITY);self.assertTrue(q.PAPER_ONLY)
if __name__=="__main__":unittest.main(verbosity=2)
