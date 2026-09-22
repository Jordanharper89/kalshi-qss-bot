import unittest
from qseries_v2.oracle_adapters.kalshi.oad_013_market_data_normalization import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_013_kalshi_orderbook_trade_ticker_normalization())
    def test_snapshot(self):
        x=normalize_kalshi_market_data({"type":"orderbook_snapshot","sid":1,"seq":1,"msg":{"market_ticker":"A","yes_dollars_fp":[["0.5","1.0"]],"no_dollars_fp":[]}},10)
        self.assertEqual(x.event_type,"orderbook_snapshot")
    def test_bad_type(self):
        with self.assertRaises(ValueError): normalize_kalshi_market_data({"type":"fill","msg":{"market_ticker":"A"}},10)
if __name__=="__main__":
    print("="*72);print(" OAD-013 CERTIFICATION TEST");print(" ORDERBOOK / TRADE / TICKER EVENT NORMALIZATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi public market-data event normalization certified");print("[DONE] OAD-013 CERTIFIED")
