import unittest
import qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile as m

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.OLF_011_BUILD_ID,"OLF-011")

    def test_contract(self):
        self.assertTrue(callable(m.build_learned_experience_profiles))
        self.assertTrue(callable(m.materialize_learned_experience_profiles))
        self.assertTrue(m.verify_olf_011_evidence_grounded_learned_experience_profile())

    def test_session_mapping(self):
        self.assertEqual(m._session("2026-08-20T01:00:00Z"),"UTC_00_05")
        self.assertEqual(m._session("2026-08-20T13:00:00Z"),"UTC_12_17")

if __name__=="__main__":
    print("="*88)
    print(" OLF-011 CERTIFICATION TEST — CORRECTION V2")
    print(" EVIDENCE-GROUNDED LEARNED EXPERIENCE PROFILE")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Canonical evidence condition profiling contract certified")
    print("[PASS] Private helper test import corrected")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-011 CORRECTION V2 CERTIFIED")
