\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_365_solana_checkpoint_after_readback_enforcement import *

class T(unittest.TestCase):
    def test_admit(self):
        proof=SimpleNamespace(highest_contiguous_accounted_slot=104,safe_to_advance=True)
        rec=SimpleNamespace(reconciliation_state="POST_COMMIT_RECONCILED")
        x=admit_checkpoint_after_readback(100,proof,rec)
        print("[CHECKPOINT-ADMIT]",x.current_checkpoint,"->",x.admitted_checkpoint,x.state)
        self.assertEqual(x.admitted_checkpoint,104)
    def test_block(self):
        proof=SimpleNamespace(highest_contiguous_accounted_slot=104,safe_to_advance=True)
        rec=SimpleNamespace(reconciliation_state="POST_COMMIT_READBACK_INCOMPLETE")
        x=admit_checkpoint_after_readback(100,proof,rec)
        self.assertEqual(x.admitted_checkpoint,100)
        self.assertEqual(x.state,"BLOCKED_READBACK")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-365 checkpoint advancement now requires exact post-commit readback + continuity")

