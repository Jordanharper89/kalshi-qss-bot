\

import unittest,tempfile
from qseries_v2.oracle_adapters.independent.oad_361_solana_restart_backfill_reconciliation import *
from qseries_v2.oracle_adapters.independent.oad_359_solana_immutable_gap_lineage_ledger import verify_gap_lineage
class T(unittest.TestCase):
    def test_restart(self):
        with tempfile.TemporaryDirectory() as d:
            x=reconcile_restart_window(100,104,(101,103,104),(102,),d)
            print("[RESTART]",x.checkpoint_before,"->",x.checkpoint_after,x.state,x.skipped_slots); self.assertEqual(x.checkpoint_after,104)
            ok,n=verify_gap_lineage(d); self.assertTrue(ok); self.assertEqual(n,1)
    def test_gap_stops(self):
        with tempfile.TemporaryDirectory() as d:
            x=reconcile_restart_window(100,104,(101,103,104),(),d); self.assertEqual(x.checkpoint_after,101); self.assertEqual(x.state,"BACKFILL_REQUIRED")
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-361 restart/downtime/backfill reconciliation certified")

