import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_204_crypto_continuous_learning_failure_isolation_recovery as m
from qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy
class T(unittest.TestCase):
    def test_failure_then_recovery(self):
        ok=SimpleNamespace(physical_ready=True,checkpoint_after=9)
        with patch.object(m,"run_crypto_continuous_learning_worker_cycle",side_effect=[RuntimeError("network"),ok]):
            sleeps=[]
            s=m.run_resilient_crypto_learning_worker(
                policy=build_crypto_continuous_learning_worker_policy(cadence_seconds=1,failure_backoff_base_seconds=2),
                max_attempts=2,progress=None,sleep_fn=lambda x:sleeps.append(x)
            )
        print("[SUCCESS]",s.successful_cycles); print("[FAILED]",s.failed_cycles); print("[CHECKPOINT]",s.last_checkpoint)
        self.assertEqual((s.successful_cycles,s.failed_cycles),(1,1))
        self.assertEqual(s.last_checkpoint,9)
        self.assertEqual(sleeps,[2.0])
        self.assertFalse(s.degraded)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-204 isolated failure/backoff/recovery worker behavior certified")
