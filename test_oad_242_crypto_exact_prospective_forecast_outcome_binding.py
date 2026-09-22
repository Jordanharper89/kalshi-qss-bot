import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_242_crypto_exact_prospective_forecast_outcome_binding as m
class Cur:
 def __init__(self,rows):self.rows=iter(rows)
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def execute(self,*a,**k):pass
 def fetchall(self):return next(self.rows)
class C:
 def __init__(self,r):self.c=Cur(r)
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def cursor(self):return self.c
 def rollback(self):pass
class T(unittest.TestCase):
 def test_exact_unique(self):
  ch="c"*64;f=(10,None,"crypto_prospective_internal_forecast",{"forecast_id":"f"*64,"asset":"BTC","created_at":"2026-09-01T00:00:00+00:00","training_snapshot_hash":ch,"horizon_seconds":60,"internal_forecast_probability":.6,"source_claims":(("coinbase",1,.6,True),)});l=(20,None,"crypto_verified_learned_case",{"asset":"BTC","experience_id":"e1","condition_hash":ch,"horizon_seconds":60,"outcome_observed_at":"2026-09-01T00:01:00+00:00","exact_interval":True,"learning_event_id":"id","learning_event_hash":"a"*64,"outcome_hash":"b"*64})
  with patch.object(m,"connect",return_value=C([(f,),(),(),(),(),(l,)])):r=m.read_exact_prospective_bindings()
  print("[BINDINGS]",len(r));self.assertEqual(len(r),1)
  with patch.object(m,"connect",return_value=C([(f,),(),(),(),(),(l,l)])):self.assertEqual(m.read_exact_prospective_bindings(),())
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-242 unique identity binding; ambiguity rejected")
