import unittest
from qseries_v2.oracle_continuous_intake.oci_009_pipeline_assembly import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_oci_009_continuous_intelligence_pipeline_assembly())
 def test_terminal_independent(self): self.assertFalse(build_oci_009_certification_manifest()["terminal_dependency"])
 def test_path(self): self.assertEqual(build_oci_009_certification_manifest()["path"],"PostgreSQL->OCI->OI->UMD->OML")
if __name__=="__main__":
 print("="*72);print(" OCI-009 CERTIFICATION TEST");print(" CONTINUOUS INTELLIGENCE PIPELINE ASSEMBLY");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Terminal-independent OCI->OI->UMD->OML pipeline assembly certified");print("[DONE] OCI-009 CERTIFIED")
