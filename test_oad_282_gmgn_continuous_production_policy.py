import unittest
from qseries_v2.oracle_adapters.independent.oad_282_gmgn_continuous_production_policy import *

class T(unittest.TestCase):
    def test_policy(self):
        p=default_gmgn_continuous_policy()
        self.assertTrue(verify_gmgn_continuous_policy(p))
        self.assertEqual(p.cadence_seconds,60.0)
        self.assertFalse(p.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-282 GMGN continuous production policy certified")
