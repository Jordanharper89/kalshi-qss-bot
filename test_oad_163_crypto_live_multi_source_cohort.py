import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_163_crypto_live_multi_source_cohort as m

class T(unittest.TestCase):
    def test_exact_target_coinbase_products(self):
        rows={
            "BTC-USD":{"price":"60000","trade_id":1,"time":"2026-08-29T00:00:00Z"},
            "ETH-USD":{"price":"3000","trade_id":2,"time":"2026-08-29T00:00:01Z"},
            "SOL-USD":{"price":"150","trade_id":3,"time":"2026-08-29T00:00:02Z"},
        }
        def get(url,timeout):
            pid=url.split("/products/")[1].split("/ticker")[0]
            return rows[pid]
        with patch.object(m,"coinbase_get_json",side_effect=get):
            obs=m.acquire_target_coinbase_crypto_observations()
        print("[TARGETS]",tuple(x.subject for x in obs))
        self.assertEqual(tuple(x.subject for x in obs),("BTC-USD","ETH-USD","SOL-USD"))
        self.assertTrue(all(x.independent_evidence is False for x in obs))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-163 exact BTC/ETH/SOL Coinbase targeting certified")
