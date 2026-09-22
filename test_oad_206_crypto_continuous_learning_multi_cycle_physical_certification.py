import unittest
from qseries_v2.oracle_adapters.independent.oad_206_crypto_continuous_learning_multi_cycle_physical_certification import run_crypto_continuous_learning_multi_cycle_physical_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_continuous_learning_multi_cycle_physical_certification()
        print("[PHYSICAL] checkpoint_start=",r.checkpoint_start)
        print("[PHYSICAL] checkpoint_end=",r.checkpoint_end)
        print("[PHYSICAL] cycles_completed=",r.cycles_completed)
        print("[PHYSICAL] experiences_formed=",r.experiences_formed)
        print("[PHYSICAL] exact_outcomes=",r.exact_outcomes)
        print("[PHYSICAL] learned_cases_committed=",r.learned_cases_committed)
        print("[PHYSICAL] checkpoint_advances=",r.checkpoint_advances)
        print("[PHYSICAL] restart_resume_verified=",r.restart_resume_verified)
        print("[PHYSICAL] cycle_states=",r.cycle_states)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        self.assertTrue(r.physical_ready)
        self.assertEqual(r.checkpoint_end,r.checkpoint_start+r.cycles_completed)
        self.assertEqual(r.checkpoint_advances,r.cycles_completed)
        self.assertTrue(r.restart_resume_verified)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-206 repeated-cycle + restart-safe crypto learning physically certified")
    print("[PASS] no synthetic outcomes; probability/direction/execution remain disabled")
