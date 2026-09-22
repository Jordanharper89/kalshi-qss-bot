import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_237_crypto_prospective_learning_cycle_activation as m
class T(unittest.TestCase):
 def test_ordered_cycle(self):
  calls=[]
  with patch.object(m,"persist_prospective_forecasts",side_effect=lambda r=None:(calls.append("forecast") or SimpleNamespace(forecasts=3,committed_new=3))), \
       patch.object(m,"run_crypto_continuous_learning_worker_cycle",side_effect=lambda *a,**k:(calls.append("base") or SimpleNamespace(checkpoint_before=10,checkpoint_after=11,experiences_formed=3,exact_outcomes=3,learned_cases_committed=3,physical_ready=True))), \
       patch.object(m,"read_and_score_mature_prospective_cases",side_effect=lambda r=None:(calls.append("score") or (1,2))):
   x=m.run_prospective_learning_cycle()
  print("[ORDER]",calls,"[SCORED]",x.scored_cases)
  self.assertEqual(calls,["forecast","base","score"]);self.assertTrue(x.physical_ready);self.assertFalse(x.execution_authority)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-237 forecast-before-outcome cycle activation certified")
