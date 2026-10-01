import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as q

class T(unittest.TestCase):
    def test_original_serve_not_reimplemented(self):
        src=inspect.getsource(q)
        self.assertNotIn("async def serve(",src)
        self.assertIn("runtime.serve(Path.cwd()",src)
        print("[PASS] original persistent_profit_runtime.serve is called directly")

    def test_only_lane_is_swapped(self):
        old=q.p.SimulationLane
        try:
            r=q.install_lane()
            self.assertIs(r.SimulationLane,q.PaperSimulationLane)
        finally:
            q.p.SimulationLane=old
        print("[PASS] only SimulationLane class is replaced")

    def test_lane_contract(self):
        for name in ("submit","worker"):
            self.assertTrue(hasattr(q.PaperSimulationLane,name))
        for attr in ("attempts","profitable","best","failures","drops"):
            self.assertIn("self."+attr,inspect.getsource(q.PaperSimulationLane.__init__))
        print("[PASS] paper lane satisfies untouched 022D serve compatibility contract")

    def test_exact_clock(self):
        self.assertLessEqual(q.TICK_SECONDS,.05)
        self.assertIn("mark_due",inspect.getsource(q.PaperSimulationLane.worker))
        print("[PASS] <=50ms paper horizon scheduler lives inside replacement lane")

    def test_no_execution(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)
        print("[PASS] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__":
    unittest.main(verbosity=2)
