import unittest
from qseries_v2.oracle_adapters.independent.oad_191_crypto_durable_learning_statistics_physical_certification import run_crypto_durable_learning_statistics_physical_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_durable_learning_statistics_physical_certification()
        print("[PHYSICAL] persisted_experiences=",r.persisted_experiences)
        print("[PHYSICAL] mature_experiences=",r.mature_experiences)
        print("[PHYSICAL] exact_outcomes=",r.exact_outcomes)
        print("[PHYSICAL] learned_cases_written=",r.learned_cases_written)
        print("[PHYSICAL] exact_readback=",r.exact_readback)
        print("[PHYSICAL] historical_learned_cases=",r.historical_learned_cases)
        print("[PHYSICAL] statistics_groups=",r.statistics_groups)
        print("[PHYSICAL] assets=",r.assets)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        self.assertTrue(r.physical_ready); self.assertGreater(r.exact_outcomes,0); self.assertFalse(r.probability_enabled); self.assertFalse(r.direction_enabled); self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-191 durable exact-horizon crypto learning statistics physically certified")
    print("[PASS] statistics are descriptive historical frequencies only; probability/direction/execution remain disabled")
