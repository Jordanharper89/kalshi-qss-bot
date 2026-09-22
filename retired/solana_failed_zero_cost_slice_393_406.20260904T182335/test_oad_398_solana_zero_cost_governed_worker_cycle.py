import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent.oad_398_solana_zero_cost_governed_worker_cycle import run_governed_solana_worker_cycle
from qseries_v2.oracle_adapters.independent.oad_393_solana_zero_cost_public_rpc_budget_governor import SolanaPublicRpcBudgetGovernor,SolanaRpcBudgetPolicy

class T(unittest.TestCase):
    def test_governed_cycle(self):
        g=SolanaPublicRpcBudgetGovernor(SolanaRpcBudgetPolicy(min_spacing_seconds=0,total_requests_per_window=10,per_method_requests_per_window=10),clock=lambda:100.0)
        with patch("qseries_v2.oracle_adapters.independent.oad_398_solana_zero_cost_governed_worker_cycle._invoke_existing_worker",return_value={"state":"COMMITTED"}):
            x=run_governed_solana_worker_cycle(governor=g)
        print("[GOVERNED CYCLE]",x)
        self.assertTrue(x.admitted)
        self.assertEqual(x.raw_type,"dict")

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-398 governed existing-worker cycle certified")