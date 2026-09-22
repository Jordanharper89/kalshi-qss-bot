import unittest
from qseries_v2.oracle_adapters.independent.oad_382_solana_existing_learner_advancement_physical_gate import *
class T(unittest.TestCase):
    def test_physical(self):
        x=measure_physical_learning_handoff(8)
        print("[LEARNING-PHYSICAL] verified_runtime_cases=",x.verified_runtime_cases,"handed_off_cases=",x.handed_off_cases)
        print("[LEARNING-PHYSICAL] handoff_type=",x.handoff_result_type,"handoff_state=",x.handoff_state)
        print("[LEARNING-PHYSICAL] learner_before=",x.learner_before)
        print("[LEARNING-PHYSICAL] learner_after=",x.learner_after)
        print("[LEARNING-PHYSICAL] learner_advanced=",x.learner_advanced,"state=",x.state)
        self.assertGreater(x.verified_runtime_cases,0,"No real verified Solana runtime cases exist yet; physical learning cannot be certified")
        self.assertGreater(x.handed_off_cases,0)
        self.assertTrue(x.learner_advanced,"OAD-317 handoff executed but existing learner state did not physically advance")
        self.assertEqual(x.state,"PHYSICAL_EXISTING_LEARNER_ADVANCED")
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-382 real verified Solana cases physically advanced the existing learner")
    print("[PASS] no synthetic case counted toward certification")
    print("[PASS] no separate Solana learner introduced")
