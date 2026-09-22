import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import OutcomeCalibrationRecord
from qseries_v2.oracle_learning_runtime.olr_026_durable_calibration_ledger import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_olr_026_durable_calibration_ledger())
    def test_persistence(self):
        c=OutcomeCalibrationRecord("KX",.7,1,.09,.3,"p",True,False)
        r=build_durable_calibration_record(c,"obs","settle")
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json"
            save_calibration_ledger(p,{r.record_id:r})
            self.assertEqual(load_calibration_ledger(p)[r.record_id],r)

if __name__=="__main__":
    print("="*72);print(" OLR-026 CERTIFICATION TEST");print(" DURABLE CALIBRATION LEDGER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Durable idempotent calibration ledger certified")
    print("[DONE] OLR-026 CERTIFIED")
