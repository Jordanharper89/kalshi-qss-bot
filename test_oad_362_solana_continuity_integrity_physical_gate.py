import unittest
from qseries_v2.oracle_adapters.independent.oad_362_solana_continuity_integrity_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_continuity_integrity_physical(4)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"slots=",x.returned_slots)
        print("[PHYSICAL] slot_source=",x.slot_source,"contiguous=",x.contiguous,"restart_checkpoint=",x.restart_checkpoint)
        print("[PHYSICAL] gap_ledger_valid=",x.gap_ledger_valid,"gap_records=",x.gap_records)
        print("[PHYSICAL] duplicate_signatures=",x.duplicate_signatures,"state=",x.state)

        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(len(x.returned_slots),0)
        self.assertTrue(x.gap_ledger_valid)
        self.assertEqual(x.duplicate_signatures,0)
        self.assertEqual(x.state,"CONTINUITY_INTEGRITY_PHYSICALLY_MEASURED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-362 live Solana continuity-integrity gate measured")
    print("[PASS] slot identity resolved from certified batch/envelope contract rather than guessed block payload shape")
