\

import unittest
from qseries_v2.oracle_adapters.independent.oad_366_solana_restart_backfill_idempotency_guard import *

class T(unittest.TestCase):
    def test_replay(self):
        x=reconcile_restart_idempotency(("a","b"),("b","c","c","d"))
        print("[IDEMPOTENCY]",x.duplicate_with_existing_ids,x.duplicate_replay_ids,x.accepted_new_ids,x.state)
        self.assertEqual(x.accepted_new_ids,("c","d"))
        self.assertTrue(x.idempotent)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-366 restart/backfill duplicate suppression and idempotency guard certified")

