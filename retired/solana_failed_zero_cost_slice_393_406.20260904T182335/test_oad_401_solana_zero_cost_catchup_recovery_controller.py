import unittest
from qseries_v2.oracle_adapters.independent.oad_401_solana_zero_cost_catchup_recovery_controller import plan_zero_cost_catchup,catchup_cycles_for_lag
class T(unittest.TestCase):
    def test_plan(self):
        x=plan_zero_cost_catchup(100,150,max_slots=8)
        print("[CATCHUP]",x)
        self.assertEqual(x.lag,50)
        self.assertEqual(len(x.batch_slots),8)
        self.assertEqual(x.state,"BOUNDED_CATCHUP")
        self.assertEqual(catchup_cycles_for_lag(50,16),4)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-401 zero-cost catch-up recovery controller certified")