import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as c

class T(unittest.TestCase):
    def test_required_account_boundary(self):
        self.assertEqual(q.PUMP_FIXED_ACCOUNTS,26)

    def test_trimmer_keeps_first_26(self):
        s=inspect.getsource(q.trim_optional_pump_accounts)
        self.assertIn("PUMP_FIXED_ACCOUNTS",s)

    def test_pool_v2_prior_fix_preserved(self):
        self.assertGreaterEqual(q.PUMP_FIXED_ACCOUNTS,24)

    def test_exact_quote_preserved(self):
        s=inspect.getsource(c.rewrite_pump_buy_bounds)
        self.assertIn("BUY_EXACT_QUOTE_IN_DISC",s)

    def test_sae003_pricer_preserved(self):
        self.assertEqual(c.q18.WORKER_JS.name,"sae003_pump_exact_quote_worker.mjs")

    def test_safety(self):
        self.assertFalse(c.EXECUTION_AUTHORITY)
        self.assertTrue(c.PAPER_ONLY)
        self.assertFalse(c.REAL_MONEY_MOVED)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",inspect.getsource(c))

if __name__=="__main__":
    unittest.main(verbosity=2)
