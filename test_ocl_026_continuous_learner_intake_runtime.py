import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_026_continuous_learner_intake_runtime())
    def test_ordering(self):
        a=build_runtime_input(2,"x","a","a"*64,{"x":1})
        b=build_runtime_input(1,"x","b","b"*64,{"x":2})
        self.assertEqual(assemble_runtime_batch((a,b)).start_sequence,1)
    def test_duplicate(self):
        a=build_runtime_input(1,"x","a","a"*64,{"x":1})
        with self.assertRaises(ValueError): assemble_runtime_batch((a,a))

if __name__=="__main__":
    print("="*72);print(" OCL-026 CERTIFICATION TEST");print(" CONTINUOUS LEARNER INTAKE RUNTIME");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic continuous learner intake runtime certified")
    print("[DONE] OCL-026 CERTIFIED")
