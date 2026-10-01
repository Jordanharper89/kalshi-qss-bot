import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_032_mriya_pool_live_update_probe as q
class T(unittest.TestCase):
    def test_shard(self):self.assertEqual([len(x) for x in q.chunks(list(range(80)))],[35,35,10])
    def test_processed(self):self.assertIn('"commitment":"processed"',inspect.getsource(q.worker))
    def test_read_only(self):self.assertNotIn("sendTransaction",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
