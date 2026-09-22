import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_154_bitcoin_mempool_fee_pressure_acquisition as m
class T(unittest.TestCase):
    def test_mapping(self):
        def get(url,timeout):
            if url.endswith("/mempool"): return {"count":1000,"vsize":2000000,"total_fee":123,"fee_histogram":[[1,2]]}
            if url.endswith("/recommended"): return {"fastestFee":10,"halfHourFee":8,"hourFee":5,"economyFee":2,"minimumFee":1}
            if url.endswith("/recent"): return [{"txid":"a","fee":1000,"vsize":200,"value":50000}]
            raise AssertionError(url)
        with patch.object(m,"_get_json",side_effect=get):
            r=m.acquire_bitcoin_mempool_pressure_observations()
        print("[OBSERVATIONS]",len(r)); print("[MEMPOOL_COUNT]",r[0].payload["count"]); print("[RECENT]",len(r[1].payload["recent_transactions"]))
        self.assertEqual(len(r),2); self.assertEqual(r[0].payload["count"],1000)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-154 Bitcoin mempool/fee-pressure acquisition certified")
