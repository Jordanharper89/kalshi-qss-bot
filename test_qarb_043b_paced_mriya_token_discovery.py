import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_043b_paced_mriya_token_discovery as q
class T(unittest.TestCase):
    def test_confirmed(self):self.assertIn('"commitment":"confirmed"',inspect.getsource(q))
    def test_queue_decouples_ws_from_rpc(self):
        s=inspect.getsource(q.serve);self.assertIn("asyncio.Queue",s);self.assertIn("consumer",s)
    def test_rate_limit_and_backoff(self):
        self.assertGreaterEqual(q.RPC_GAP,.5);self.assertIn("RPC_429_BACKOFF",inspect.getsource(q.rpc_retry))
    def test_failed_tx_not_marked_done(self):
        s=inspect.getsource(q.paced_backfill);self.assertLess(s.index("await fetch_and_ingest"),s.index("done.add(sig)"))
    def test_wsol_excluded(self):
        tx={"meta":{"preTokenBalances":[{"mint":q.WSOL},{"mint":"T"}],"postTokenBalances":[]}}
        self.assertEqual(q.tx_mints(tx),["T"])
    def test_read_only(self):self.assertFalse(q.EXECUTION_AUTHORITY);self.assertTrue(q.READ_ONLY)
if __name__=="__main__":unittest.main(verbosity=2)
