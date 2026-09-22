\

import unittest
from qseries_v2.oracle_adapters.independent.oad_358_solana_skipped_slot_safe_checkpoint import *
class T(unittest.TestCase):
    def test_skip_is_accounted(self):
        p=prove_contiguous_slot_accounting(100,104,(100,101,103,104),(102,))
        print("[CONTIGUOUS]",p.highest_contiguous_accounted_slot,p.skipped_slots,p.safe_to_advance)
        self.assertEqual(safe_checkpoint_target(p,99),104); self.assertTrue(p.safe_to_advance)
    def test_missing_stops_checkpoint(self):
        p=prove_contiguous_slot_accounting(100,104,(100,101,103,104),())
        self.assertEqual(p.highest_contiguous_accounted_slot,101); self.assertEqual(safe_checkpoint_target(p,99),101)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-358 skipped-slot-aware contiguous checkpoint advancement certified")

