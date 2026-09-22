import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_203_crypto_continuous_learning_repeated_cycle_worker as m
class T(unittest.TestCase):
 def test_worker_identity(self):
  x=SimpleNamespace(checkpoint_before_cycle=1,checkpoint_after_cycle=2,experiences_formed=1,exact_outcomes=0,learned_cases_committed=0,cycle_state="OBSERVE_WAITING_FOR_OUTCOMES",physical_ready=True,experience_ids=("crypto-exp:BTC:x",))
  with patch.object(m,"run_crypto_continuous_learning_cycle",return_value=x):r=m.run_crypto_continuous_learning_worker_cycle(policy=SimpleNamespace(horizon_seconds=60,persistence_timeout_seconds=120,acquisition_timeout_seconds=20))
  print("[IDS]",r.experience_ids);self.assertEqual(r.experience_ids,x.experience_ids)
if __name__=="__main__":
 x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not x.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-248 worker exact identity propagation certified")
