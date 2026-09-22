import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_201_crypto_continuous_learning_24x7_physical_certification as m
class T(unittest.TestCase):
 def test_ids_propagate_without_behavior_change(self):
  cp=SimpleNamespace(cycle_sequence=7,state_hash="a"*64)
  formation=SimpleNamespace(committed_new=1,exact_readback=1,snapshot_at="x",assets=("BTC",),physical_ready=True,experience_ids=("crypto-exp:BTC:abc",))
  learned=SimpleNamespace(exact_outcomes=0,committed_new=0,exact_readback=0,assets=(),physical_ready=True)
  nxt=SimpleNamespace(cycle_sequence=8,state_hash="b"*64)
  with patch.object(m,"read_checkpoint",return_value=cp),patch.object(m,"form_continuous_crypto_experience_cycle",return_value=formation),patch.object(m,"form_continuous_verified_learned_cases",return_value=learned),patch.object(m,"advance_checkpoint",return_value=nxt),patch.object(m,"write_checkpoint",return_value=nxt):
   r=m.run_crypto_continuous_learning_cycle()
  print("[EXPERIENCE_IDS]",r.experience_ids);self.assertEqual(r.experience_ids,formation.experience_ids);self.assertTrue(r.physical_ready)
if __name__=="__main__":
 x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not x.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-247 foundational cycle identity exposure certified")
