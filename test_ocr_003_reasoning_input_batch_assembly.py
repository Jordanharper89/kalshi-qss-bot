import unittest
from qseries_v2.oracle_continuous_reasoning.ocr_003_reasoning_input_batch import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocr_003_reasoning_input_batch_assembly())
    def test_duplicate(self):
        row={"observation_id":"x","payload":{"market_ticker":"A"}}
        with self.assertRaises(ValueError): assemble_reasoning_input_batch((row,row))
if __name__=="__main__":
    print("="*72);print(" OCR-003 CERTIFICATION TEST");print(" REASONING INPUT BATCH ASSEMBLY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic live-observation reasoning batches certified")
    print("[DONE] OCR-003 CERTIFIED")
