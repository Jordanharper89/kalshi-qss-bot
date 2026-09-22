
import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_007_learning_event_ledger import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_007_durable_learning_event_ledger())
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json";r=LearningLedgerRecord("a"*64,"K","t","learned","b"*64,"c"*64)
            save_learning_ledger(p,{r.settlement_hash:r});self.assertEqual(load_learning_ledger(p)[r.settlement_hash],r)
if __name__=="__main__":
    print("="*72);print(" OLR-007 CERTIFICATION TEST");print(" DURABLE LEARNING EVENT LEDGER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Durable idempotent learning-event ledger certified");print("[DONE] OLR-007 CERTIFIED")
