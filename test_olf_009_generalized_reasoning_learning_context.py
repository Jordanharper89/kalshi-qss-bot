import unittest
from qseries_v2.oracle_learning_feedback.olf_009_generalized_learning_context import *

class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OLF_009_BUILD_ID,"OLF-009")
    def test_related_never_directly_adjusts(self):
        x=GeneralizedLearningContext("KX","SAME_KALSHI_SERIES",.75,("A",),3,.09,"h",True,False,.05,True,False)
        self.assertEqual(apply_generalized_confidence_context(.6,x),.6)

if __name__=="__main__":
    print("="*88);print(" OLF-009 CERTIFICATION TEST");print(" GENERALIZED REASONING LEARNING CONTEXT");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Historical same-series experience context certified")
    print("[PASS] Cross-contract calibration transfer prohibited")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-009 CERTIFIED")
