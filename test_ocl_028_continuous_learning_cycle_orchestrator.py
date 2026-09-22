import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import genesis_incremental_state
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_028_continuous_learning_cycle_orchestrator())
    def test_terminal_independent(self):
        b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
        r,_=run_learning_cycle(1,genesis_incremental_state(),b);self.assertFalse(r.terminal_dependency)
    def test_cycle_advances(self):
        b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
        _,s=run_learning_cycle(1,genesis_incremental_state(),b);self.assertEqual(s.applied_through_sequence,1)

if __name__=="__main__":
    print("="*72);print(" OCL-028 CERTIFICATION TEST");print(" CONTINUOUS LEARNING CYCLE ORCHESTRATOR");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Terminal-independent 24/7 learning-cycle orchestration certified")
    print("[DONE] OCL-028 CERTIFIED")
