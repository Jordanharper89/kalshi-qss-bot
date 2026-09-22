import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_203_crypto_continuous_learning_repeated_cycle_worker as m
from qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy
class T(unittest.TestCase):
    def test_repeated_cycles(self):
        seq=[
            SimpleNamespace(checkpoint_before_cycle=4,checkpoint_after_cycle=5,experiences_formed=3,exact_outcomes=0,learned_cases_committed=0,cycle_state="OBSERVE_WAITING_FOR_OUTCOMES",physical_ready=True),
            SimpleNamespace(checkpoint_before_cycle=5,checkpoint_after_cycle=6,experiences_formed=3,exact_outcomes=3,learned_cases_committed=3,cycle_state="LEARNED_NEW_CASES",physical_ready=True),
        ]
        with patch.object(m,"run_crypto_continuous_learning_cycle",side_effect=seq):
            sleeps=[]
            last=m.run_crypto_continuous_learning_worker(
                policy=build_crypto_continuous_learning_worker_policy(cadence_seconds=1),
                max_cycles=2,progress=None,sleep_fn=lambda x:sleeps.append(x)
            )
        print("[FINAL_CHECKPOINT]",last.checkpoint_after); print("[SLEEPS]",sleeps)
        self.assertEqual(last.checkpoint_after,6)
        self.assertEqual(sleeps,[1.0])
        self.assertFalse(last.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-203 repeated continuous-learning worker cycle certified")
