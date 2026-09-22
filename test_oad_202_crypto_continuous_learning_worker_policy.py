import unittest
from qseries_v2.oracle_adapters.independent.oad_202_crypto_continuous_learning_worker_policy import build_crypto_continuous_learning_worker_policy,failure_backoff_seconds
class T(unittest.TestCase):
    def test_policy(self):
        p=build_crypto_continuous_learning_worker_policy()
        vals=tuple(failure_backoff_seconds(p,n) for n in (1,2,3,10))
        print("[CADENCE]",p.cadence_seconds); print("[BACKOFF]",vals)
        self.assertEqual(vals[:3],(2.0,4.0,8.0))
        self.assertEqual(vals[-1],60.0)
        self.assertFalse(p.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-202 continuous-learning worker cadence/backoff policy certified")
