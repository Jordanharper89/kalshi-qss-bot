import unittest
from qseries_v2.oracle_adapters.kalshi.oad_017_keepalive_liveness import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_017_kalshi_keepalive_liveness_supervision())
    def test_stale_reconnect(self):
        s=evaluate_keepalive(0,0,26_000_000_000)
        self.assertTrue(should_reconnect_keepalive(s))
    def test_recent_healthy(self):
        s=evaluate_keepalive(10_000_000_000,10_000_000_001,15_000_000_000)
        self.assertTrue(s.healthy)
if __name__=="__main__":
    print("="*72);print(" OAD-017 CERTIFICATION TEST");print(" KALSHI KEEPALIVE + CONNECTION LIVENESS SUPERVISION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi Ping/Pong liveness supervision certified");print("[DONE] OAD-017 CERTIFIED")
