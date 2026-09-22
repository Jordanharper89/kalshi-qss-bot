import unittest
from qseries_v2.oracle_adapters.independent.oad_196_crypto_weighted_historical_learning_physical_certification import run_crypto_weighted_historical_learning_physical_certification
class T(unittest.TestCase):
    def test_physical(self):
        r=run_crypto_weighted_historical_learning_physical_certification()
        print("[PHYSICAL] historical_learned_cases=",r.historical_learned_cases)
        print("[PHYSICAL] raw_statistics_groups=",r.raw_statistics_groups)
        print("[PHYSICAL] sufficiency_profiles=",r.sufficiency_profiles)
        print("[PHYSICAL] recency_profiles=",r.recency_profiles)
        print("[PHYSICAL] regime_profiles=",r.regime_profiles)
        print("[PHYSICAL] uncertainty_profiles=",r.uncertainty_profiles)
        print("[PHYSICAL] insufficient_groups=",r.insufficient_groups)
        print("[PHYSICAL] mature_descriptive_groups=",r.mature_descriptive_groups)
        print("[PHYSICAL] assets=",r.assets)
        print("[PHYSICAL] physical_ready=",r.physical_ready)
        self.assertTrue(r.physical_ready)
        self.assertGreater(r.historical_learned_cases,0)
        self.assertFalse(r.probability_enabled)
        self.assertFalse(r.direction_enabled)
        self.assertFalse(r.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-196 weighted historical crypto learning physically certified")
    print("[PASS] insufficient samples remain explicit; no probability/direction/execution enabled")
