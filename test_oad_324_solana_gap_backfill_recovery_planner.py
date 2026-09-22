\

import tempfile,unittest
from qseries_v2.oracle_adapters.independent.oad_323_solana_durable_slot_checkpoint import commit_solana_chain_checkpoint
from qseries_v2.oracle_adapters.independent.oad_324_solana_gap_backfill_recovery_planner import *
class T(unittest.TestCase):
 def test_gap(self):
  with tempfile.TemporaryDirectory() as d:
   commit_solana_chain_checkpoint(100,"s",d)
   p=build_solana_recovery_plan(105,d)
   print("[RECOVERY]",p.mode,p.start_slot,p.end_slot,"gap=",p.gap_slots)
   self.assertEqual((p.start_slot,p.end_slot,p.gap_slots),(101,105,5));self.assertEqual(p.mode,"BACKFILL")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-324 recoverable finalized-slot gap planning certified")

