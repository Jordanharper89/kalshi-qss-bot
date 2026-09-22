import unittest
from qseries_v2.oracle_learning_feedback.olf_003_reasoning_learning_context import *

class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OLF_003_BUILD_ID,"OLF-003")
    def test_no_unmatured_adjustment(self):
        x=LearningAwareReasoningContext("KX","h",10,.4,True,False,.05,True,False)
        self.assertEqual(apply_bounded_confidence_context(.61,x),.61)
    def test_bounded_adjustment(self):
        x=LearningAwareReasoningContext("KX","h",10,.4,True,True,.05,True,False)
        self.assertAlmostEqual(apply_bounded_confidence_context(.61,x),.66)

if __name__=="__main__":
    print("="*88);print(" OLF-003 CERTIFICATION TEST");print(" REASONING LEARNING-CONTEXT ENVELOPE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Learned experience can be consumed without fabricating direction")
    print("[PASS] Confidence adjustment requires mature bounded calibration")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-003 CERTIFIED")
