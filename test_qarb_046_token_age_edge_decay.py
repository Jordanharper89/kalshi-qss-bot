import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_046_token_age_edge_decay as q
class T(unittest.TestCase):
    def test_buckets(self):
        self.assertEqual(q.age_bucket(20),"0-60s");self.assertEqual(q.age_bucket(120),"1-3m")
        self.assertEqual(q.age_bucket(400),"3-10m");self.assertEqual(q.age_bucket(1200),"10-30m")
    def test_no_execution(self):self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
