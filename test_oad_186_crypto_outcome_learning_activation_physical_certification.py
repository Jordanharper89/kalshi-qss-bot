import unittest
from qseries_v2.oracle_adapters.independent.oad_186_crypto_outcome_learning_activation_physical_certification import run_crypto_outcome_learning_activation_physical_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_outcome_learning_activation_physical_certification()
        print("[PHYSICAL] persisted_experiences=",r.persisted_experiences)
        print("[PHYSICAL] mature_experiences=",r.mature_experiences)
        print("[PHYSICAL] outcomes=",r.outcomes)
        print("[PHYSICAL] verified_learning_events=",r.verified_learning_events)
        print("[PHYSICAL] intake_ready=",r.intake_ready)
        print("[PHYSICAL] assets=",r.assets)
        print("[PHYSICAL] horizon_seconds=",r.horizon_seconds)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        self.assertTrue(r.physical_ready)
        self.assertGreater(r.mature_experiences,0)
        self.assertEqual(r.outcomes,r.mature_experiences)
        self.assertEqual(r.verified_learning_events,r.mature_experiences)
        self.assertEqual(r.intake_ready,r.mature_experiences)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-186 crypto outcome + verified OCL LearningEvent activation physically certified")
    print("[PASS] real horizon expiration required; no synthetic outcomes; probability/direction/execution remain disabled")
