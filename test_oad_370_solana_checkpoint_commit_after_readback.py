\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_370_solana_checkpoint_commit_after_readback import *

class T(unittest.TestCase):
    def test_commit(self):
        proof=SimpleNamespace(highest_contiguous_accounted_slot=104,safe_to_advance=True)
        rec=SimpleNamespace(reconciliation_state="POST_COMMIT_RECONCILED")
        with patch("qseries_v2.oracle_adapters.independent.oad_370_solana_checkpoint_commit_after_readback.commit_checkpoint_exact") as c:
            x=commit_checkpoint_after_exact_readback(100,proof,rec)
            c.assert_called_once()
        print("[CHECKPOINT-COMMIT]",x.before_slot,"->",x.committed_slot,x.state)
        self.assertEqual(x.state,"CHECKPOINT_PHYSICALLY_COMMITTED")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-370 physical checkpoint commit requires exact readback admission")

