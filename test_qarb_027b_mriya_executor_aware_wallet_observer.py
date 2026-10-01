import unittest,inspect
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_027b_mriya_executor_aware_wallet_observer as q
class T(unittest.TestCase):
    def test_executor(self):self.assertEqual(q.EXECUTOR,"AN225ykGPAmckE9uMCCM7jQv3L3AYwiPZbHqgMUYEgCR")
    def test_retry(self):self.assertIn("attempts=6",inspect.getsource(q.rpc))
    def test_full_rows(self):self.assertIn("account_index",inspect.getsource(q.token_rows))
    def test_read_only(self):self.assertNotIn("sendTransaction",inspect.getsource(q))
if __name__=="__main__":unittest.main(verbosity=2)
