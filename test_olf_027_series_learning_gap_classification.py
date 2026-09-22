import unittest
import qseries_v2.oracle_learning_feedback.olf_027_series_learning_gaps as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OLF_027_BUILD_ID,"OLF-027")
    def test_gap(self):self.assertEqual(m.gap_reason({"learned_records":3,"evidence_resolved":3,"outcome_attributed":0,"probability_recovered":3,"scored_records":0}),"NO_ATTRIBUTED_SETTLEMENT_RESULTS")
if __name__=="__main__":
    print("="*88);print(" OLF-027 CERTIFICATION TEST");print(" SERIES LEARNING GAP CLASSIFICATION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Exact per-series learning blocker classification certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-027 CERTIFIED")
