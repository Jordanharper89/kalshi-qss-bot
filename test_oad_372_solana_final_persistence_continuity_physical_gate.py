\

import unittest
from qseries_v2.oracle_adapters.independent.oad_372_solana_final_persistence_continuity_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_final_persistence_continuity(4)
        print("[FINAL-PHYSICAL] worker=",x.worker_symbol,"writer_started_by_gate=",x.writer_started_by_gate)
        print("[FINAL-PHYSICAL] cycles=",x.cycles,"successful=",x.successful_cycles)
        print("[FINAL-PHYSICAL] checkpoint=",x.checkpoint_before,"->",x.checkpoint_after,"advanced=",x.checkpoint_advanced)
        print("[FINAL-PHYSICAL] transactions=",x.total_transactions,"observations=",x.total_observations,"committed=",x.total_committed)
        print("[FINAL-PHYSICAL] gap_ledger_valid=",x.gap_ledger_valid,"gap_records=",x.gap_records,"state=",x.state)
        self.assertEqual(x.cycles,4)
        self.assertEqual(x.successful_cycles,4)
        self.assertTrue(x.checkpoint_advanced)
        self.assertTrue(x.gap_ledger_valid)
        self.assertEqual(x.state,"FINAL_PERSISTENCE_CONTINUITY_CERTIFIED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-372 final Solana persistence + durable checkpoint advancement physically certified")
    print("[PASS] certified OPH-021 writer boundary used and stopped only if started by this gate")
    print("[PASS] next boundary is temporal/outcome/learning integration")

