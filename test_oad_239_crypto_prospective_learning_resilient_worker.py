import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_239_crypto_prospective_learning_resilient_worker as m
from qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy
class T(unittest.TestCase):
    def test_recovery(self):
        ok=SimpleNamespace(physical_ready=True,checkpoint_after=9,scored_cases=1,forecasts=3,forecasts_committed=3)
        refresh=SimpleNamespace(admission_state="HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED")
        p=build_crypto_continuous_learning_worker_policy(cadence_seconds=1,failure_backoff_base_seconds=2)
        with patch.object(m,"run_prospective_learning_cycle",side_effect=[RuntimeError("network"),ok]), patch.object(m,"refresh_prospective_learning_states",return_value=refresh):
            sleeps=[]
            s=m.run_resilient_prospective_learning_worker(policy=p,max_attempts=2,progress=None,sleep_fn=lambda x:sleeps.append(x))
        print("[SUCCESS]",s.successful_cycles,"[FAILED]",s.failed_cycles,"[CHECKPOINT]",s.last_checkpoint,"[SLEEPS]",sleeps)
        self.assertEqual((s.successful_cycles,s.failed_cycles),(1,1)); self.assertEqual(s.last_checkpoint,9)
        self.assertEqual(s.last_scored_cases,1); self.assertEqual(sleeps,[2.0]); self.assertFalse(s.degraded); self.assertFalse(s.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-239 exact OAD-204-compatible backoff/recovery semantics certified")
