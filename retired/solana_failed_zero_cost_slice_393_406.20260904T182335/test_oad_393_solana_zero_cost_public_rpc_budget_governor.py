import unittest
from qseries_v2.oracle_adapters.independent.oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaRpcBudgetPolicy,SolanaPublicRpcBudgetGovernor
class T(unittest.TestCase):
    def test_budget(self):
        now=[100.0]
        g=SolanaPublicRpcBudgetGovernor(SolanaRpcBudgetPolicy(total_requests_per_window=3,per_method_requests_per_window=2,min_spacing_seconds=0),clock=lambda:now[0])
        self.assertTrue(g.admit("getBlock"))
        self.assertTrue(g.admit("getBlock"))
        self.assertFalse(g.admit("getBlock"))
        self.assertTrue(g.admit("getSlot"))
        self.assertFalse(g.admit("getBlocks"))
        g.record_throttle(4.0)
        self.assertGreaterEqual(g.wait_seconds("getSlot"),4.0)
        print("[BUDGET]",g.snapshot())
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-393 zero-cost public RPC budget governor certified")