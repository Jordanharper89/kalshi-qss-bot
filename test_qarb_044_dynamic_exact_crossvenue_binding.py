import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_044_dynamic_exact_crossvenue_binding as q
class T(unittest.TestCase):
    def test_canonical_seed(self):
        s=inspect.getsource(q.canonical_pump_pool);self.assertIn('b"pool-authority"',s);self.assertIn('b"pool"',s)
    def test_exact_gates(self):
        s=inspect.getsource(q.verify);self.assertIn("base_mint",s);self.assertIn("quote_mint",s);self.assertIn("token_x",s)
    def test_no_execution(self):self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
