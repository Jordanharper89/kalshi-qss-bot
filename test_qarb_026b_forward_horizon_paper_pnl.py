import tempfile,unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026b_forward_horizon_paper_pnl as q

class T(unittest.TestCase):
    def setUp(self):
        self.old_h=q.HORIZONS
        q.HORIZONS=(2.0,5.0)

    def tearDown(self):
        q.HORIZONS=self.old_h

    def test_forward_only_not_instant(self):
        p=SimpleNamespace(token="T",last_slot=10)
        old_buy=q.live._pump_buy
        q.live._pump_buy=lambda pair,start:1000
        try:
            with tempfile.TemporaryDirectory() as td:
                b=q.Book(td,100)
                d={"direction":"PUMP_TO_METEORA","size_sol":1.0,"net_sol":0.02,"net_bps":200.0}
                pos=b.enter(p,d,100.0)
                self.assertIsNotNone(pos)
                self.assertEqual(len(b.closed),0)
                self.assertEqual(b.update_pair(p,101.0),[])
        finally:
            q.live._pump_buy=old_buy
        print("[PASS] entry quote is never booked as realized paper PNL")

    def test_exact_horizons_use_future_mark(self):
        p=SimpleNamespace(token="T",last_slot=10)
        old_buy=q.live._pump_buy
        old_q=q.live._dlmm_quote
        q.live._pump_buy=lambda pair,start:1000
        q.live._dlmm_quote=lambda pair,qty,mint:1_100_000_000
        try:
            with tempfile.TemporaryDirectory() as td:
                b=q.Book(td,0)
                d={"direction":"PUMP_TO_METEORA","size_sol":1.0,"net_sol":0.02,"net_bps":200.0}
                b.enter(p,d,100.0)
                self.assertEqual(len(b.update_pair(p,101.9)),0)
                r=b.update_pair(p,102.1)
                self.assertEqual(len(r),1)
                self.assertEqual(r[0]["horizon_seconds"],2.0)
                self.assertEqual(b.by_h[2.0]["trades"],1)
                self.assertEqual(b.by_h[5.0]["trades"],0)
        finally:
            q.live._pump_buy=old_buy
            q.live._dlmm_quote=old_q
        print("[PASS] horizon closes only from later market state")

    def test_no_execution_or_simulation(self):
        import inspect
        src=inspect.getsource(q)
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        self.assertNotIn("simulateTransaction",src)
        self.assertNotIn("qsb059",src)
        print("[PASS] no simulator/composer path; execution_authority=FALSE")

if __name__=="__main__":
    unittest.main(verbosity=2)
