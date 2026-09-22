import unittest
from qseries_v2.oracle_scientific_reasoning.osr_026_reasoning_calibration import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_osr_026_reasoning_calibration_engine())

    def test_poor_calibration(self):
        x = assess_reasoning_calibration((CalibrationObservation("a", 1.0, 0.0, 1.0),))
        self.assertEqual(x.status, "poor")

    def test_bounds(self):
        with self.assertRaises(ValueError):
            assess_reasoning_calibration((CalibrationObservation("a", 2.0, 0.0, 1.0),))

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-026 CERTIFICATION TEST")
    print(" REASONING CALIBRATION ENGINE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Evidence-aware reasoning calibration certified")
    print("[DONE] OSR-026 CERTIFIED")
