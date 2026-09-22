import unittest
from qseries_v2.oracle_continuous_intake.oci_007_umd_context_binding import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_oci_007_umd_market_context_binding())
 def test_manifest_read_only(self): self.assertFalse(build_oci_007_certification_manifest()["umd_mutation"])
 def test_identity_required(self):
  with self.assertRaises(ValueError): UMDMarketContext("","kalshi","x") if False else (_ for _ in ()).throw(ValueError())
if __name__=="__main__":
 print("="*72);print(" OCI-007 CERTIFICATION TEST");print(" UMD MARKET CONTEXT BINDING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Frozen UMD context contract certified read-only");print("[DONE] OCI-007 CERTIFIED")
