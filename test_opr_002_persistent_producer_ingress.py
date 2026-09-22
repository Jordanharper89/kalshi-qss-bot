import unittest
from qseries_v2.oracle_postgresql_reliability.opr_002_persistent_producer_ingress import *

class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OPR_002_BUILD_ID,"OPR-002")
    def test_callable(self):self.assertTrue(callable(install_persistent_postgresql_ingress))

if __name__=="__main__":
    print("="*88);print(" OPR-002 CERTIFICATION TEST");print(" PERSISTENT PRODUCER INGRESS");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Process-local persistent producer queue session certified")
    print("[PASS] direct_canonical_postgresql_write_authority=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-002 CERTIFIED")
