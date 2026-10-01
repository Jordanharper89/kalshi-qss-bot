import inspect,unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026g_token_freshness_profit_audit as q

class T(unittest.TestCase):
    def test_venue_classification(self):
        self.assertEqual(q._venue("PUMP_BASE"),"PUMPSWAP")
        self.assertEqual(q._venue("PUMP_QUOTE"),"PUMPSWAP")
        self.assertEqual(q._venue("DLMM_POOL"),"METEORA_DLMM")
        self.assertEqual(q._venue("DLMM_ARRAY_3"),"METEORA_DLMM")
        print("[PASS] PumpSwap and Meteora account events classified separately")

    def test_original_apply_is_preserved(self):
        src=inspect.getsource(q.tracked_apply)
        self.assertIn("_ORIG_APPLY(",src)
        print("[PASS] freshness wrapper delegates to original apply_account_event")

    def test_original_runtime_not_reimplemented(self):
        src=inspect.getsource(q)
        self.assertNotIn("async def serve(",src)
        self.assertIn("runtime.serve(Path.cwd()",src)
        print("[PASS] persistent_profit_runtime.serve remains source of truth")

    def test_observation_only(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        self.assertIn("[TOKEN_SCORE]",inspect.getsource(q.FreshnessPaperLane.worker))
        self.assertIn("[ENTRY_FRESHNESS]",inspect.getsource(q.FreshnessPaperLane.submit))
        print("[PASS] per-token PNL + entry freshness observation installed")

if __name__=="__main__":
    unittest.main(verbosity=2)
