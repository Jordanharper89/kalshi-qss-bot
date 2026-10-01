import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060a_live_transaction_correlated_shadow_validator as q
class T(unittest.TestCase):
    def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_tolerance(self):self.assertEqual(q.MAX_ERROR_BPS,10.0)
    def test_vault_direction(self):
        p={"family":"X","pool":"P","vault_a":"A","vault_b":"B"}
        self.assertTrue(q.EXECUTION_AUTHORITY is False)
if __name__=="__main__":unittest.main(verbosity=2)
