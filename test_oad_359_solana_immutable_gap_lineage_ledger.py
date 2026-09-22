\

import unittest,tempfile
from qseries_v2.oracle_adapters.independent.oad_359_solana_immutable_gap_lineage_ledger import *
class T(unittest.TestCase):
    def test_chain(self):
        with tempfile.TemporaryDirectory() as d:
            a=append_gap_lineage(10,12,"SKIPPED_SLOTS",(11,),d); b=append_gap_lineage(13,15,"RECOVERABLE_GAP",(14,15),d)
            ok,n=verify_gap_lineage(d); print("[GAP-LEDGER]",n,a.record_hash[:12],b.previous_hash[:12]); self.assertTrue(ok); self.assertEqual(n,2)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-359 immutable hash-chained Solana gap lineage certified")

