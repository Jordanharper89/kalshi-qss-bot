import unittest
from qseries_v2.oracle_adapters.independent.oad_256_crypto_derivatives_open_interest_funding_intelligence import *
class T(unittest.TestCase):
 def test_derivatives(self):
  def f(url,timeout): return {"retCode":0,"result":{"list":[{"lastPrice":"100","markPrice":"99","indexPrice":"98","openInterest":"10","openInterestValue":"1000","fundingRate":"0.0001","nextFundingTime":"1","volume24h":"20","turnover24h":"2000"}]}}
  x=acquire_derivatives_state(fetch=f); print("[DERIVATIVES]",x.payload["open_interest"],x.payload["funding_rate"]); self.assertEqual(x.payload["symbol"],"BTCUSDT")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-256 derivatives open-interest/funding intelligence certified")
