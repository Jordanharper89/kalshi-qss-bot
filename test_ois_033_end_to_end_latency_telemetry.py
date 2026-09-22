import unittest
from qseries_v2.oracle_intelligence_state.ois_031_low_latency_event_intake import build_canonical_market_event
from qseries_v2.oracle_intelligence_state.ois_033_latency_telemetry import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_033_end_to_end_latency_telemetry())

    def test_segments_sum(self):
        e=build_canonical_market_event("k","a","m","trade",0,10,1,"a"*64)
        x=measure_event_latency(e,20,30,40)
        self.assertEqual(x.end_to_end_ns,x.venue_to_oracle_ns+x.oracle_to_shadow_ns+x.shadow_to_evaluation_ns+x.evaluation_to_handoff_ns)

    def test_nonmonotonic(self):
        e=build_canonical_market_event("k","a","m","trade",0,10,1,"a"*64)
        with self.assertRaises(ValueError):
            measure_event_latency(e,9,30,40)

if __name__=="__main__":
    print("="*72);print(" OIS-033 CERTIFICATION TEST");print(" END-TO-END LATENCY TELEMETRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Venue-to-Oracle-to-Q-Series-handoff latency telemetry certified")
    print("[DONE] OIS-033 CERTIFIED")
