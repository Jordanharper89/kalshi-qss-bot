import unittest
from qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import build_canonical_market_event
from qseries_v2.oracle_intelligence_state.ois_032_event_classification import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_032_market_event_classification())

    def test_trade_normal(self):
        e=build_canonical_market_event("k","a","m","trade",1,2,1,"a"*64)
        self.assertEqual(classify_market_event(e).urgency,"NORMAL")

    def test_unknown_other(self):
        e=build_canonical_market_event("k","a","m","mystery",1,2,1,"a"*64)
        self.assertEqual(classify_market_event(e).event_class,"OTHER")

if __name__=="__main__":
    print("="*72);print(" OIS-032 CERTIFICATION TEST");print(" MARKET EVENT CLASSIFICATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Canonical transaction/market-event classification certified")
    print("[DONE] OIS-032 CERTIFIED")
