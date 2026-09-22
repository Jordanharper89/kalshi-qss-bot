import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_243_crypto_mature_prospective_case_registry as m
class T(unittest.TestCase):
 def test_lineage_gate(self):
  g=SimpleNamespace(forecast_id="f",asset="BTC",experience_id="e",condition_hash="c"*64,forecast_probability=.6,source_claims=(),learning_event_id="id",learning_event_hash="a"*64,outcome_hash="b"*64);b=SimpleNamespace(**{**g.__dict__,"learning_event_hash":"bad"})
  with patch.object(m,"read_exact_prospective_bindings",return_value=(g,b)):r=m.build_mature_prospective_case_registry()
  print("[MATURE]",len(r));self.assertEqual(len(r),1)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-243 mature exact registry certified")
