import unittest
from qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_ocr_012_incremental_new_observation_selection())
    def test_numeric_cursor_ordering_contract(self):
        self.assertEqual(build_incremental_cursor_predicate("sequence_number"),"numeric")

    def test_timestamp_cursor_ordering_contract(self):
        self.assertEqual(build_incremental_cursor_predicate("persisted_at"),"timestamp")

    def test_cursor_values(self):
        s=IncrementalObservationSlice("s","t","sequence_number",({"sequence_number":7,"observation_id":"o7"},))
        self.assertEqual(cursor_values_from_last_row(s),("sequence_number","7","o7"))
if __name__=="__main__":
    print("="*72);print(" OCR-012 CERTIFICATION TEST");print(" INCREMENTAL NEW-OBSERVATION SELECTION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] SELECT-only incremental observation selection certified");print("[DONE] OCR-012 CERTIFIED")
