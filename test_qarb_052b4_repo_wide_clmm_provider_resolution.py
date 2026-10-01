import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052b4_repo_wide_clmm_provider_resolution as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY); self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_names(self): self.assertIn("quote_exact_in",q.QUOTE_NAMES)
if __name__=="__main__":unittest.main(verbosity=2)
