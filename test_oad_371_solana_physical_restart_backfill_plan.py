\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_371_solana_physical_restart_backfill_plan import *

class T(unittest.TestCase):
    def test_plan(self):
        with patch("qseries_v2.oracle_adapters.independent.oad_371_solana_physical_restart_backfill_plan.discover_checkpoint_contract",return_value=SimpleNamespace(current_slot=100)):
            with patch("qseries_v2.oracle_adapters.independent.oad_371_solana_physical_restart_backfill_plan.reconcile_restart_window",return_value=SimpleNamespace(state="RECONCILED_TO_HEAD")):
                x=build_physical_restart_plan(103,(101,102,103),("a",),("a","b"))
        print("[RESTART-PLAN]",x.checkpoint_before,"->",x.finalized_head,x.restart_state,x.accepted_new_ids)
        self.assertTrue(x.replay_idempotent)
        self.assertEqual(x.accepted_new_ids,("b",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-371 persisted-checkpoint restart/backfill idempotency plan certified")

