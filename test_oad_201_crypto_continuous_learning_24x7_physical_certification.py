import unittest
from qseries_v2.oracle_adapters.independent.oad_201_crypto_continuous_learning_24x7_physical_certification import run_crypto_continuous_learning_24x7_physical_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_continuous_learning_24x7_physical_certification()
        print("[PHYSICAL] checkpoint_before_cycle=",r.checkpoint_before_cycle)
        print("[PHYSICAL] checkpoint_after_cycle=",r.checkpoint_after_cycle)
        print("[PHYSICAL] experiences_formed=",r.experiences_formed)
        print("[PHYSICAL] formation_exact_readback=",r.formation_exact_readback)
        print("[PHYSICAL] exact_outcomes=",r.exact_outcomes)
        print("[PHYSICAL] learned_cases_committed=",r.learned_cases_committed)
        print("[PHYSICAL] learned_case_exact_readback=",r.learned_case_exact_readback)
        print("[PHYSICAL] restart_checkpoint_verified=",r.restart_checkpoint_verified)
        print("[PHYSICAL] assets=",r.assets)
        print("[PHYSICAL] cycle_state=",r.cycle_state)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        self.assertTrue(r.physical_ready)
        self.assertEqual(r.checkpoint_after_cycle,r.checkpoint_before_cycle+1)
        self.assertTrue(r.restart_checkpoint_verified)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-201 restart-safe continuous crypto learning cycle physically certified")
    print("[PASS] new experiences mature through real time; no synthetic outcomes; probability/direction/execution remain disabled")
