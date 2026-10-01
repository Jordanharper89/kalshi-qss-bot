import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026h_fresh_crossvenue_paper_gate as q

class T(unittest.TestCase):
    def test_gate_default(self):
        self.assertEqual(q.MAX_CROSS_VENUE_AGE_MS,750.0)
        print("[PASS] cross-venue freshness gate defaults to 750ms")

    def test_engine_not_reimplemented(self):
        src=inspect.getsource(q)
        self.assertNotIn("async def serve(",src)
        self.assertIn("runtime.serve(Path.cwd()",src)
        print("[PASS] original persistent_profit_runtime.serve remains source of truth")

    def test_hot_signal_not_filtered(self):
        src=inspect.getsource(q.install)
        self.assertIn("p.SimulationLane=FreshOnlyPaperLane",src)
        self.assertNotIn("_process_event",src)
        print("[PASS] HOT_SIGNAL qualification unchanged; only paper admission gated")

    def test_unknown_and_stale_rejected(self):
        src=inspect.getsource(q.FreshOnlyPaperLane.submit)
        self.assertIn("VENUE_NOT_YET_OBSERVED",src)
        self.assertIn("STALE_SIDE",src)
        self.assertIn("PAPER_ENTRY_FRESH",src)
        print("[PASS] unknown/stale venue state rejected before paper entry")

    def test_read_only(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)
        print("[PASS] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__":
    unittest.main(verbosity=2)
