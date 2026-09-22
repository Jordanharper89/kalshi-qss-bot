import unittest
from qseries_v2.oracle_adapters.kalshi.oad_011_websocket_foundation import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_011_kalshi_websocket_market_data_foundation())
    def test_command(self):
        c=build_subscribe_command(7,("orderbook_delta",),("A","B"))
        self.assertEqual(c["params"]["market_tickers"],["A","B"])
    def test_private_channel_rejected(self):
        with self.assertRaises(ValueError): build_subscribe_command(1,("fill",),("A",))
if __name__=="__main__":
    print("="*72);print(" OAD-011 CERTIFICATION TEST");print(" KALSHI WEBSOCKET MARKET-DATA FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Authenticated read-only Kalshi WebSocket market-data foundation certified");print("[DONE] OAD-011 CERTIFIED")
