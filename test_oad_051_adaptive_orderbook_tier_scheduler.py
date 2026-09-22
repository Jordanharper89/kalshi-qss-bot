import unittest
from qseries_v2.oracle_adapters.kalshi.oad_051_adaptive_orderbook_tier_scheduler import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_051_adaptive_orderbook_tier_scheduler())
    def test_priority(self):
        p=build_adaptive_orderbook_tier_plan({"A":"WARM","B":"ULTRA_HOT","C":"ACTIVE"},2)
        self.assertEqual(p.active_tickers,("B","C"))
if __name__=="__main__":
    print("="*72);print(" OAD-051 CERTIFICATION TEST");print(" ADAPTIVE ORDERBOOK TIER SCHEDULER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Adaptive orderbook tier scheduler certified")
    print("[DONE] OAD-051 CERTIFIED")
