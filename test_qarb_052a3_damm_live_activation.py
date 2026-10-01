import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a3_damm_live_activation as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_aliases(self): self.assertIn("vault_a",q.ALIASES)
if __name__=="__main__":unittest.main(verbosity=2)
