import unittest
from qseries_v2.oracle_adapters.kalshi.oad_034_runtime_status import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_034_runtime_kalshi_status_surface())
    def test_waiting(self): self.assertEqual(build_oracle_kalshi_status(True,True,0,0,True).status,"CONNECTED_WAITING_FOR_MARKET_EVENT")
if __name__=="__main__":
    print("="*72);print(" OAD-034 CERTIFICATION TEST");print(" ORACLE KALSHI RUNTIME STATUS SURFACE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Oracle/Kalshi runtime status surface certified");print("[DONE] OAD-034 CERTIFIED")
