import unittest
from qseries_v2.oracle_learning_runtime.olr_015_learned_state_feedback_runtime_gate import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_olr_015_learned_state_feedback_runtime_gate())
    def test_no_execution_authority(self):
        if 15 == 15:
            p=LearnedStateProjection("KX",1,1,0,1.0,0.5)
            self.assertFalse(run_learned_state_feedback_cycle(p,0.5).execution_authority)
        else:
            self.assertTrue(True)

if __name__=="__main__":
    print("="*72)
    print(" OLR-015 CERTIFICATION TEST")
    print(" LEARNED-STATE FEEDBACK RUNTIME GATE")
    print("="*72)
    unittest.main(verbosity=2)
