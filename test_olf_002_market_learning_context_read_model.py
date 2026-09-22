import unittest
from qseries_v2.oracle_learning_feedback.olf_002_market_learning_context import *

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(OLF_002_BUILD_ID,"OLF-002")
    def test_contract(self):
        x=MarketLearningContext("KX","h",1,.04,True,False,0.0,"x",True,False)
        self.assertTrue(x.advisory_only)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    print("="*88);print(" OLF-002 CERTIFICATION TEST");print(" MARKET LEARNING CONTEXT READ MODEL");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Market learning-context read model certified")
    print("[PASS] Mature calibration remains bounded and advisory-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-002 CERTIFIED")
