import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052c3_orca_provider_binding as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_venue(self): self.assertEqual(q.VENUE,"ORCA_WHIRLPOOL")
if __name__=="__main__":unittest.main(verbosity=2)
