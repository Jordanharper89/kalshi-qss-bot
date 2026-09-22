import unittest
from qseries_v2.oracle_adapters.kalshi.oad_026_persistent_stream_runner import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_026_persistent_kalshi_live_stream_runner())
    def test_backoff_cap(self): self.assertEqual(next_reconnect_delay(20,build_persistent_stream_config()),30.0)
    def test_read_only(self): self.assertFalse(build_persistent_stream_config().execution_authority)
if __name__=="__main__":
    print("="*72);print(" OAD-026 CERTIFICATION TEST");print(" PERSISTENT KALSHI LIVE STREAM RUNNER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Persistent Kalshi live-stream runner policy certified");print("[DONE] OAD-026 CERTIFIED")
