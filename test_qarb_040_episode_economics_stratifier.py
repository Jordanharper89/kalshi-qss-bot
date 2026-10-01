import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_040_episode_economics_stratifier as q
class T(unittest.TestCase):
    def test_buckets(self):
        self.assertEqual(q.size_bucket(.05),"<=0.05");self.assertEqual(q.bps_bucket(200),">=200")
        self.assertEqual(q.skew_bucket(500),"250-500ms")
if __name__=="__main__":unittest.main(verbosity=2)
