import unittest
from qseries_v2.oracle_historical_learning.ohl_002_postgresql_historical_observation_read_boundary import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ohl_002_postgresql_historical_observation_read_boundary())
    def test_identifier_rejected(self):
        with self.assertRaises(ValueError): safe_identifier("x;drop")
    def test_limit_contract(self):
        with self.assertRaises(ValueError): build_historical_read_spec(limit=10001)

if __name__=="__main__":
    print("="*72)
    print(" OHL-002 CERTIFICATION TEST")
    print(" POSTGRESQL HISTORICAL OBSERVATION READ BOUNDARY")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Postgresql Historical Observation Read Boundary certified")
    print("[DONE] OHL-002 CERTIFIED")
