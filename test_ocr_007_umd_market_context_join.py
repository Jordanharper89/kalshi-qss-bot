import unittest
from qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_ocr_007_umd_market_context_join())
    def test_read_only(self):self.assertTrue(join_rows_to_umd_context(({"observation_id":"o","ticker":"KXTEST"},))[0].umd_read_only)
if __name__=="__main__":
    print("="*72);print(" OCR-007 CERTIFICATION TEST");print(" UMD MARKET CONTEXT JOIN");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Frozen OCI-007 UMD context contract joined to recovered markets");print("[DONE] OCR-007 CERTIFIED")
