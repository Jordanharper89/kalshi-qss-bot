import unittest
from qseries_v2.oracle_learning_runtime.olr_031_calibration_candidate_intake import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_olr_031_calibration_candidate_intake())

    def test_contract(self):
        x=CalibrationCandidateBatch(2,1,1,1,tuple())
        self.assertEqual(x.probability_abstentions,1)

if __name__=="__main__":
    print("="*72)
    print(" OLR-031 CERTIFICATION TEST")
    print(" CALIBRATION CANDIDATE INTAKE")
    print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Learned-settlement + exact-evidence calibration intake certified")
    print("[PASS] Missing defensible probability remains abstention")
    print("[DONE] OLR-031 CERTIFIED")
