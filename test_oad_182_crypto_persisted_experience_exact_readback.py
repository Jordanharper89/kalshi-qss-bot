import unittest
from datetime import datetime,timezone
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_182_crypto_persisted_experience_exact_readback as m
class Fake:
    backend_id="fake"
    def __init__(self): self.requests=[]
    def query(self,request):
        self.requests.append(request)
        asset=request.source_id.rsplit(".",1)[-1].upper()
        return (SimpleNamespace(
            observation_id="obs-"+asset,source_id=request.source_id,
            observation_type="crypto_historical_experience_candidate",
            observed_at=datetime(2026,8,29,2,0,0,tzinfo=timezone.utc),
            payload=tuple({
                "experience_id":"exp-"+asset,"asset":asset,"snapshot_at":"2026-08-29T02:00:00+00:00",
                "cohort_state":"FULL_COVERAGE","condition_vector":(("coinbase","spot_price",100.0,"OBSERVED"),),
                "temporal_vector":(("coinbase","spot_price","INCREASED",1.0,1.0,True),),
                "evidence_hash":"a"*64,"condition_hash":"b"*64,"experience_hash":"c"*64,
                "lineage_hash":"d"*64,"outcome_attached":False
            }.items())
        ),)
class T(unittest.TestCase):
    def test_exact_sources(self):
        b=Fake()
        with patch.object(m,"_backend",return_value=b):
            r=m.read_persisted_crypto_experiences(assets=("BTC","ETH","SOL"),per_asset_limit=16)
        print("[QUERY_TYPES]",tuple(x.query_type for x in b.requests))
        print("[SOURCES]",tuple(x.source_id for x in b.requests))
        print("[EXPERIENCES]",r.experiences)
        self.assertEqual(r.experiences,3)
        self.assertTrue(all(x.query_type=="by_source_id" for x in b.requests))
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-182 exact persisted crypto experience readback certified")
