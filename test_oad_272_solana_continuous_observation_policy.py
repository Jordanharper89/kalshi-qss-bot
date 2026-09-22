import unittest
from qseries_v2.oracle_adapters.independent.oad_272_solana_continuous_observation_policy import *

class T(unittest.TestCase):
    def test_policy(self):
        p=build_solana_continuous_observation_policy()
        print("[TICK_SECONDS]",p.tick_seconds)
        print("[ACQUISITION_SECONDS]",p.acquisition_seconds)
        print("[WINDOWS]",p.windows_seconds)
        self.assertEqual(p.tick_seconds,1.0)
        self.assertEqual(p.acquisition_seconds,5.0)
        self.assertEqual(p.windows_seconds,(5,15,30,60))
        self.assertTrue(verify_solana_continuous_observation_policy(p))
        self.assertFalse(p.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-272 1-second internal tick + source-safe acquisition policy certified")
    print("[PASS] 1-second tick is not a 1-second REST polling requirement")
