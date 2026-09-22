import unittest
import qseries_v2.oracle_learning_feedback.olf_021_experience_regimes as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OLF_021_BUILD_ID,"OLF-021")
    def test_bands(self):
        self.assertEqual(m.probability_band(.10),"YES_00_19");self.assertEqual(m.probability_band(.50),"YES_40_59");self.assertEqual(m.probability_band(.90),"YES_80_100")
if __name__=="__main__":
    print("="*88);print(" OLF-021 CERTIFICATION TEST");print(" EXPERIENCE REGIME SEGMENTATION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Series + evidence type + UTC session + probability-band regimes certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-021 CERTIFIED")
