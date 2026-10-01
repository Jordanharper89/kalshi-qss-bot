import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q
class T(unittest.TestCase):
    def test_mode(self):
        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_cap(self):
        s=q.capped_valves(list(range(256)))
        self.assertEqual(len(s),4)
        self.assertTrue(all(len(x)<=64 for x in s))
    def test_preserves_all_accounts(self):
        s=q.capped_valves(list(range(257)))
        self.assertEqual(sum(map(len,s)),257)
if __name__=="__main__":
    unittest.main(verbosity=2)
