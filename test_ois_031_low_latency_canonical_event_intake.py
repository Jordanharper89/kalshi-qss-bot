import unittest
from qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_031_low_latency_canonical_event_intake())

    def test_receive_after_event(self):
        with self.assertRaises(ValueError):
            build_canonical_market_event("k","a","m","trade",10,9,1,"a"*64)

    def test_deterministic(self):
        a=build_canonical_market_event("k","a","m","trade",10,12,1,"a"*64)
        b=build_canonical_market_event("k","a","m","trade",10,12,1,"a"*64)
        self.assertEqual(a.event_hash,b.event_hash)

if __name__=="__main__":
    print("="*72);print(" OIS-031 CERTIFICATION TEST");print(" LOW-LATENCY CANONICAL EVENT INTAKE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Low-latency canonical market-event intake certified")
    print("[DONE] OIS-031 CERTIFIED")
