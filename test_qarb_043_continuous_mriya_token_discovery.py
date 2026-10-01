import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_043_continuous_mriya_token_discovery as q
class T(unittest.TestCase):
    def test_confirmed(self):self.assertIn('"commitment":"confirmed"',inspect.getsource(q))
    def test_wsol_excluded(self):
        tx={"meta":{"preTokenBalances":[{"mint":q.WSOL},{"mint":"T"}],"postTokenBalances":[]}}
        self.assertEqual(q.tx_mints(tx),["T"])
    def test_event_driven(self):self.assertIn("logsSubscribe",inspect.getsource(q.serve))
    def test_read_only(self):self.assertFalse(q.EXECUTION_AUTHORITY);self.assertTrue(q.READ_ONLY)
if __name__=="__main__":unittest.main(verbosity=2)
