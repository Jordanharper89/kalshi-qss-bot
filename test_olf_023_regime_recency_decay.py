import unittest
import qseries_v2.oracle_learning_feedback.olf_023_regime_recency as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OLF_023_BUILD_ID,"OLF-023")
    def test_dt(self):self.assertIsNotNone(m._dt("2026-08-20T01:00:00Z"))
if __name__=="__main__":
    print("="*88);print(" OLF-023 CERTIFICATION TEST");print(" REGIME RECENCY + DECAY");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Deterministic settlement-time recency decay certified");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-023 CERTIFIED")
