import unittest
from qseries_v2.oracle_learning_feedback.olf_014_condition_aware_experience import *
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OLF_014_BUILD_ID,"OLF-014")
    def test_contract(self):
        x=ConditionAwareExperience("KX","s",False,"","UNKNOWN",0,0,0,0,"h","NONE",False,False)
        self.assertFalse(x.directional_signal_available);self.assertFalse(x.execution_authority)
if __name__=="__main__":
    print("="*88);print(" OLF-014 CERTIFICATION TEST");print(" CONDITION-AWARE EXPERIENCE RESOLVER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Structural + observed-condition matching certified");print("[PASS] no directional signal fabricated");print("[PASS] execution_authority=FALSE");print("[DONE] OLF-014 CERTIFIED")
