import unittest
from qseries_v2.oracle_continuous_intake.oci_008_oml_admission_binding import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_oci_008_oml_memory_admission_binding())
 def test_no_memory_write(self): self.assertFalse(build_oci_008_certification_manifest()["oml_write"])
 def test_role(self): self.assertEqual(build_oci_008_certification_manifest()["role"],"admission_candidate_only")
if __name__=="__main__":
 print("="*72);print(" OCI-008 CERTIFICATION TEST");print(" OML MEMORY ADMISSION BINDING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OML admission-candidate boundary certified without memory mutation");print("[DONE] OCI-008 CERTIFIED")
