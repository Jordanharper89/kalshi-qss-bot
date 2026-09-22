import unittest
from qseries_v2.oracle_adapters.independent.oad_272_solana_continuous_observation_policy import build_solana_continuous_observation_policy
from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import *

class T(unittest.TestCase):
    def test_backoff(self):
        p=build_solana_continuous_observation_policy(failure_backoff_base_seconds=2,failure_backoff_max_seconds=10)
        r=tuple(failure_backoff_seconds(p,x) for x in (1,2,3,4))
        print("[BACKOFF]",r)
        self.assertEqual(r,(2.0,4.0,8.0,10.0))

if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-275 resilient continuous Solana worker/backoff certified")
