\

import unittest
from qseries_v2.oracle_adapters.independent.oad_369_solana_postcommit_exact_readback_bridge import *

class T(unittest.TestCase):
    def test_bridge(self):
        obs=({"observation_id":"a"},{"observation_id":"b"})
        x=verify_committed_batch_exact_readback(obs,lambda ids:[{"observation_id":"a"},{"observation_id":"b"}])
        print("[READBACK-BRIDGE]",x.observation_ids,x.found_ids,x.missing_ids,x.reconciliation_state)
        self.assertTrue(x.exact)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-369 committed Solana batch -> exact PostgreSQL readback bridge certified")

