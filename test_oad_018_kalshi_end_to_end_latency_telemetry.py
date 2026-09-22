import unittest
from qseries_v2.oracle_adapters.kalshi.oad_018_latency_telemetry import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_018_kalshi_end_to_end_latency_telemetry())
    def test_monotonic(self):
        with self.assertRaises(ValueError): build_latency_sample(10,9,20,30)
    def test_summary(self):
        s=tuple(build_latency_sample(0,i*1_000_000,i*1_000_000+1,i*1_000_000+2) for i in (1,2,3))
        self.assertEqual(summarize_latency(s).count,3)
if __name__=="__main__":
    print("="*72);print(" OAD-018 CERTIFICATION TEST");print(" KALSHI END-TO-END LATENCY TELEMETRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi source-to-routing latency telemetry certified");print("[DONE] OAD-018 CERTIFIED")
