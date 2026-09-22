import unittest
from datetime import datetime,timezone
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_173_crypto_condition_recent_history_exact_readback as m
class Fake:
    backend_id="fake"
    def query(self,request):
        self.request=request
        return (
            SimpleNamespace(
                source_id="source.crypto.condition.eth.ethereum.gas_price_wei",
                observation_type="crypto_condition_snapshot",
                observed_at=datetime(2026,8,29,1,0,0,tzinfo=timezone.utc),
                payload=tuple({
                    "asset":"ETH","source_family":"ethereum","metric_name":"gas_price_wei",
                    "value":100.0,"unit":"wei","condition":"OBSERVED","basis":"raw",
                    "independent_evidence":True,"market_native_reference":False,
                }.items())
            ),
            SimpleNamespace(source_id="source.other",observation_type="x",observed_at=datetime(2026,8,29,1,0,0,tzinfo=timezone.utc),payload=()),
        )
class T(unittest.TestCase):
    def test_bounded_read(self):
        b=Fake()
        with patch.object(m,"_backend",return_value=b):
            r=m.read_recent_crypto_condition_history(now=datetime(2026,8,29,2,0,0,tzinfo=timezone.utc),lookback_seconds=3600,limit=100)
        print("[QUERY_TYPE]",b.request.query_type)
        print("[QUERIED]",r.queried_rows,"[CONDITIONS]",r.condition_rows)
        self.assertEqual(b.request.query_type,"by_observed_time_range")
        self.assertEqual(b.request.limit,100)
        self.assertEqual(r.condition_rows,1)
        self.assertEqual(r.states[0].asset,"ETH")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-173 bounded recent PostgreSQL condition-history readback certified")
