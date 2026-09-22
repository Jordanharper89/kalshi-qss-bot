\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_364_solana_post_commit_observation_reconciliation import *

class T(unittest.TestCase):
    def test_ok(self):
        x=reconcile_post_commit_ids(("a","b"),SimpleNamespace(found_ids=("a","b")))
        print("[POST-COMMIT]",x.reconciliation_state,x.missing_ids)
        self.assertEqual(x.reconciliation_state,"POST_COMMIT_RECONCILED")
    def test_missing(self):
        x=reconcile_post_commit_ids(("a","b"),SimpleNamespace(found_ids=("a",)))
        self.assertEqual(x.reconciliation_state,"POST_COMMIT_READBACK_INCOMPLETE")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-364 post-commit observation-ID reconciliation certified")

