import unittest
from qseries_v2.oracle_adapters.kalshi.oad_014_sequence_integrity import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_014_kalshi_sequence_integrity_gap_detection_resync())
    def test_duplicate_rejected(self): self.assertFalse(evaluate_sequence_integrity(1,5,5,"ticker").accept)
    def test_snapshot_baseline(self): self.assertTrue(evaluate_sequence_integrity(1,None,10,"orderbook_snapshot").accept)
    def test_gap_resync(self): self.assertTrue(evaluate_sequence_integrity(1,1,3,"orderbook_delta").resync_required)
if __name__=="__main__":
    print("="*72);print(" OAD-014 CERTIFICATION TEST");print(" SEQUENCE INTEGRITY + GAP DETECTION + RESYNC");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi sequence integrity/gap detection/get_snapshot resync certified");print("[DONE] OAD-014 CERTIFIED")
