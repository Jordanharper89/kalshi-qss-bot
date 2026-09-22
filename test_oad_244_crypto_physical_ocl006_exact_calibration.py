import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_244_crypto_physical_ocl006_exact_calibration as m
class T(unittest.TestCase):
 def test_event_id_semantics(self):
  b=SimpleNamespace(experience_id="e",forecast_probability=.7,learning_event_id="EVENT-ID");h=SimpleNamespace(experience_id="e",return_fraction=.01)
  with patch.object(m,"read_exact_prospective_bindings",return_value=(b,)),patch.object(m,"read_crypto_learned_case_history",return_value=(h,)),patch.object(m,"envelope",return_value=SimpleNamespace(state_hash="a"*64)):r=m.materialize_exact_prospective_calibration()
  print("[BRIER]",r.mean_brier);self.assertAlmostEqual(r.mean_brier,.09)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-244 exact OCL-006 event-id calibration certified")
