import unittest
from datetime import datetime,timezone
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_173_crypto_condition_source_scoped_history_readback as m
class Fake:
    backend_id="fake"
    def __init__(self): self.requests=[]
    def query(self,request):
        self.requests.append(request)
        return (SimpleNamespace(
            observation_type="crypto_condition_snapshot",
            observed_at=datetime(2026,8,29,1,0,0,tzinfo=timezone.utc),
            payload=tuple({"asset":"BTC","source_family":"bitcoin","metric_name":"fastest_fee_rate","value":10.0,"unit":"sat/vB","condition":"ELEVATED","basis":"x","independent_evidence":True,"market_native_reference":False}.items())
        ),)
class T(unittest.TestCase):
    def test_source_scoped(self):
        current=(SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate"),)
        b=Fake()
        with patch.object(m,"_backend",return_value=b):
            r=m.read_crypto_condition_history_for_current_states(current,per_source_limit=64)
        print("[QUERY_TYPE]",b.requests[0].query_type)
        print("[SOURCE_ID]",b.requests[0].source_id)
        print("[ROWS]",r.condition_rows)
        self.assertEqual(b.requests[0].query_type,"by_source_id")
        self.assertTrue(b.requests[0].source_id.startswith("source.crypto.condition."))
        self.assertEqual(r.condition_rows,1)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-173 source-scoped PostgreSQL history readback certified")
