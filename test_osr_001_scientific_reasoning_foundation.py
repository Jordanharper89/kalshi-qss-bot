import unittest
from qseries_v2.oracle_scientific_reasoning.osr_001_foundation import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_001_scientific_reasoning_foundation())
    def test_deterministic(self):
        a=build_scientific_reasoning_input("a"*64,"q",("c"*64,"b"*64))
        b=build_scientific_reasoning_input("a"*64,"q",("b"*64,"c"*64))
        self.assertEqual(a.input_hash,b.input_hash)
    def test_bad_hash(self):
        with self.assertRaises(ValueError): build_scientific_reasoning_input("bad","q")

if __name__=="__main__":
    print("="*72);print(" OSR-001 CERTIFICATION TEST");print(" SCIENTIFIC REASONING FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic read-only Scientific Reasoning foundation certified")
    print("[DONE] OSR-001 CERTIFIED")
