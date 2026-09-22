import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_242_crypto_exact_prospective_forecast_outcome_binding as m
class Cur:
 def __init__(self,r):self.r=iter(r)
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def execute(self,*a,**k):pass
 def fetchall(self):return next(self.r)
class C:
 def __init__(self,r):self.c=Cur(r)
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def cursor(self):return self.c
 def rollback(self):pass
class T(unittest.TestCase):
 def test_explicit_ledger_only(self):
  b=(10,{"forecast_id":"f"*64,"asset":"BTC","experience_id":"crypto-exp:BTC:x","forecast_created_at":"2026-09-01T00:00:00+00:00","horizon_seconds":60,"internal_forecast_probability":.6,"source_claims":(("coinbase",1,.6,True),)})
  l=(20,{"experience_id":"crypto-exp:BTC:x","asset":"BTC","condition_hash":"c"*64,"horizon_seconds":60,"outcome_observed_at":"2026-09-01T00:01:00+00:00","exact_interval":True,"learning_event_id":"id","learning_event_hash":"a"*64,"outcome_hash":"b"*64})
  with patch.object(m,"connect",return_value=C([(b,),(l,),(),(),(),()])):r=m.read_exact_prospective_bindings()
  print("[EXACT]",len(r),r[0].experience_id);self.assertEqual(len(r),1)
if __name__=="__main__":
 x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not x.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-251 explicit identity ledger read boundary certified")
