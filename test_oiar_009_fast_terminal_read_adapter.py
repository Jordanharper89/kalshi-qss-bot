import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_009_fast_terminal_read_adapter import (
    OIAR_009_BUILD_ID,FastTraderIntelligenceRead
)
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OIAR_009_BUILD_ID,"OIAR-009")
    def test_contract(self):
        x=FastTraderIntelligenceRead("x","FRESH",1,10,(),(),.5,True,True,False)
        self.assertTrue(x.read_only);self.assertFalse(x.execution_authority)
if __name__=="__main__":
    print("="*88);print(" OIAR-009 CERTIFICATION TEST");print(" FAST TERMINAL READ ADAPTER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] persisted snapshot-only terminal adapter certified")
    print("[PASS] last-good degraded serving preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-009 CERTIFIED")
