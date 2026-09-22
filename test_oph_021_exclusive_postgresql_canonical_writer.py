import unittest
from qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_oph_021_exclusive_postgresql_canonical_writer())
    def test_key(self):self.assertIsInstance(ADVISORY_LOCK_KEY,int)
if __name__=="__main__":
    print("="*88);print(" OPH-021 CERTIFICATION TEST");print(" EXCLUSIVE POSTGRESQL CANONICAL WRITER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Exclusive canonical writer certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-021 CERTIFIED")
