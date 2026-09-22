import unittest
from qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import build_canonical_market_event
from qseries_v2.oracle_intelligence_state.ois_039_multi_adapter_event_coordination import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_039_multi_adapter_event_stream_coordination())

    def test_order(self):
        a=build_canonical_market_event("v1","a1","m1","trade",1,5,1,"a"*64)
        b=build_canonical_market_event("v2","a2","m2","trade",1,4,1,"b"*64)
        self.assertEqual(coordinate_adapter_events((a,b))[0].adapter_id,"a2")

    def test_duplicate(self):
        a=build_canonical_market_event("v","a","m","trade",1,2,1,"a"*64)
        with self.assertRaises(ValueError):
            coordinate_adapter_events((a,a))

if __name__=="__main__":
    print("="*72);print(" OIS-039 CERTIFICATION TEST");print(" MULTI-ADAPTER EVENT-STREAM COORDINATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic multi-adapter event-stream coordination certified")
    print("[DONE] OIS-039 CERTIFIED")
