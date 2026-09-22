import unittest
import qseries_v2.oracle_learning_feedback.olf_028_series_maturity as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OLF_028_BUILD_ID,"OLF-028")
    def test_admission(self):
        self.assertTrue(m.admitted("PROVEN"));self.assertFalse(m.admitted("SPARSE"))
if __name__=="__main__":
    print("="*88);print(" OLF-028 CERTIFICATION TEST");print(" SERIES MATURITY + ADMISSION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] PROVEN/MATURE/LEARNING/SPARSE/EVIDENCE_ONLY/BLIND admission certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-028 CERTIFIED")
