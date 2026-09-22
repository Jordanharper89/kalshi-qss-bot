import unittest
from qseries_v2.oracle_adapters.kalshi.oad_024_physical_websocket import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_024_physical_kalshi_websocket_activation())
    def test_endpoint(self): self.assertTrue(build_oad_024_certification_manifest()["production_websocket"].startswith("wss://"))
if __name__=="__main__":
    print("="*72);print(" OAD-024 CERTIFICATION TEST");print(" PHYSICAL KALSHI WEBSOCKET ACTIVATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Physical authenticated Kalshi WebSocket activation implementation certified");print("[DONE] OAD-024 CERTIFIED")
