import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_143_coinbase_public_product_universe_discovery as m
class T(unittest.TestCase):
    def test_discovery(self):
        rows=[{"id":"BTC-USD","base_currency":"BTC","quote_currency":"USD","trading_disabled":False},{"id":"ETH-EUR","base_currency":"ETH","quote_currency":"EUR","trading_disabled":False},{"id":"BAD-USD","base_currency":"BAD","quote_currency":"USD","trading_disabled":True}]
        with patch.object(m,"_get_json",return_value=rows):
            r=m.discover_coinbase_public_products()
        print("[PRODUCTS]",len(r),r[0]["product_id"])
        self.assertEqual(tuple(x["product_id"] for x in r),("BTC-USD",))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-143 Coinbase public product-universe discovery certified")
