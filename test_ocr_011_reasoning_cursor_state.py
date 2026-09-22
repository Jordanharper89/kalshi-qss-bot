import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_ocr_011_reasoning_cursor_state())
    def test_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_reasoning_cursor(Path(d)/"none.json"),empty_reasoning_cursor())
if __name__=="__main__":
    print("="*72);print(" OCR-011 CERTIFICATION TEST");print(" REASONING CURSOR STATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Durable atomic reasoning cursor state certified");print("[DONE] OCR-011 CERTIFIED")
