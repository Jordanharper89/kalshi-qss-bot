
import unittest
from qseries_v2.oracle_production_hardening.oph_017_canonical_backend_rejection_forensic import verify_oph_017_canonical_backend_rejection_forensic
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oph_017_canonical_backend_rejection_forensic())
if __name__=="__main__":
    print("="*80);print(" OPH-017 CERTIFICATION TEST");print(" CANONICAL BACKEND REJECTION FORENSIC");print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OPH-017 certified");print("[DONE] OPH-017 CERTIFIED")
