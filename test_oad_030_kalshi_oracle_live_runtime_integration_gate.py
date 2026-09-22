import unittest
from qseries_v2.oracle_adapters.kalshi.oad_030_runtime_integration_gate import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_030_kalshi_oracle_live_runtime_integration_gate())
    def test_five(self): self.assertEqual(len(certify_oad_026_through_030().builds),5)
    def test_runtime(self): self.assertEqual(certify_oad_026_through_030().runtime_command,"run_oracle_LIVE.py")
if __name__=="__main__":
    print("="*72);print(" OAD-030 CERTIFICATION TEST");print(" KALSHI → ORACLE LIVE RUNTIME PRODUCTION INTEGRATION GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-026 through OAD-030 Kalshi → Oracle Live Runtime integration capability certified")
    print("[PASS] Runtime command: run_oracle_LIVE.py")
    print("[PASS] Next capability: physical runtime launcher binding + end-to-end live event persistence verification")
    print("[DONE] OAD-030 CERTIFIED")
