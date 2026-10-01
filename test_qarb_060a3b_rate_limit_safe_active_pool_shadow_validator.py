import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060a3b_rate_limit_safe_active_pool_shadow_validator as q
class T(unittest.TestCase):
    def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_gate(self):self.assertEqual(q.MAX_ERROR_BPS,10.0)
    def test_limits(self):self.assertTrue(q.CLMM_PROGRAM);self.assertTrue(q.ORCA_PROGRAM)
if __name__=="__main__":unittest.main(verbosity=2)
