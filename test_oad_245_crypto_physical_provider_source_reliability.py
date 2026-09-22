import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_245_crypto_physical_provider_source_reliability as m
class T(unittest.TestCase):
 def test_provider_only(self):
  b=SimpleNamespace(experience_id="e",source_claims=(("coinbase",1,.6,True),("condition_family",1,.8,True)));h=SimpleNamespace(experience_id="e",return_fraction=.01)
  with patch.object(m,"read_exact_prospective_bindings",return_value=(b,)),patch.object(m,"read_crypto_learned_case_history",return_value=(h,)),patch.object(m,"envelope",return_value=SimpleNamespace(state_hash="a"*64)):r=m.materialize_exact_provider_source_reliability()
  print("[SOURCES]",tuple(x.source_id for x in r.source_states),"[REJECTED]",r.rejected_non_provider_claims);self.assertEqual(tuple(x.source_id for x in r.source_states),("coinbase",));self.assertEqual(r.rejected_non_provider_claims,1)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-245 provider-only OCL-007 reliability certified")
