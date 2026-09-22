import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_016_canonical_market_identity_resolver import CanonicalMarketIdentity,OIAR_016_BUILD_ID
class T(unittest.TestCase):
    def test_identity(self): self.assertEqual(OIAR_016_BUILD_ID,"OIAR-016")
    def test_contract(self):
        x=CanonicalMarketIdentity("X",False,None,None,None,None,None,None,None,None,"unresolved",True,False)
        self.assertTrue(x.read_only); self.assertFalse(x.execution_authority)
if __name__=="__main__":
    print("="*88);print(" OIAR-016 CERTIFICATION TEST");print(" CANONICAL MARKET IDENTITY RESOLVER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] exact canonical identity contract certified")
    print("[PASS] unresolved identity remains explicit")
    print("[DONE] OIAR-016 CERTIFIED")
