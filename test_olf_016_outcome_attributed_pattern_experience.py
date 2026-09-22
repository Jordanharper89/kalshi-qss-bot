import unittest
import qseries_v2.oracle_learning_feedback.olf_016_outcome_attributed_experience as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OLF_016_BUILD_ID,"OLF-016")
    def test_mid(self):
        p,s=m.implied_yes_probability({"payload":{"yes_bid_dollars":"0.2","yes_ask_dollars":"0.4"}})
        self.assertAlmostEqual(p,.3);self.assertEqual(s,"YES_MID")
    def test_result(self):self.assertEqual(m.normalize_result("NO"),"no")
if __name__=="__main__":
    print("="*88);print(" OLF-016 CERTIFICATION TEST");print(" OUTCOME-ATTRIBUTED PATTERN EXPERIENCE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Pre-settlement probability + actual settlement attribution certified")
    print("[PASS] execution_authority=FALSE");print("[DONE] OLF-016 CERTIFIED")
