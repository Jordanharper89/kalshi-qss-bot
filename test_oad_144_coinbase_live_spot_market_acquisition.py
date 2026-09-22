import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_144_coinbase_live_spot_market_acquisition as m
class T(unittest.TestCase):
    def test_mapping(self):
        products=({"product_id":"BTC-USD","base_currency":"BTC","quote_currency":"USD"},)
        tick={"price":"60000.00","bid":"59999","ask":"60001","volume":"100","trade_id":123,"time":"2026-08-29T00:00:00Z"}
        with patch.object(m,"discover_coinbase_public_products",return_value=products),patch.object(m,"_get_json",return_value=tick):
            r=m.acquire_coinbase_live_spot_observations()
        print("[COINBASE_OBSERVATIONS]",len(r),r[0].subject,r[0].payload["price"])
        self.assertEqual(len(r),1); self.assertFalse(r[0].independent_evidence)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-144 Coinbase live spot acquisition contract certified")
