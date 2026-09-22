import unittest
from datetime import datetime,timezone
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_189_crypto_learned_case_exact_history_readback as m
class B:
    backend_id="b"
    def query(self,request):
        a=request.source_id.rsplit(".",1)[-1].upper()
        return (SimpleNamespace(observation_id="o"+a,observation_type="crypto_verified_learned_case",payload=tuple({"asset":a,"experience_id":"e"+a,"snapshot_at":"2026-08-29T00:00:00+00:00","condition_vector":(),"temporal_vector":(),"condition_hash":"a"*64,"experience_hash":"b"*64,"lineage_hash":"c"*64,"horizon_seconds":60,"outcome_observed_at":"2026-08-29T00:01:00+00:00","return_fraction":.01,"return_percent":1.0,"outcome_hash":"d"*64,"learning_event_hash":"e"*64,"exact_interval":True}.items())),)
class T(unittest.TestCase):
    def test_read(self):
        with patch.object(m,"_backend",return_value=B()): rows=m.read_crypto_learned_case_history()
        print("[ROWS]",len(rows)); print("[ASSETS]",tuple(x.asset for x in rows))
        self.assertEqual(tuple(x.asset for x in rows),("BTC","ETH","SOL"))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-189 exact learned-case history readback certified")
