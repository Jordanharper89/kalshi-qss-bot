import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import genesis_incremental_state,verify_incremental_state
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import run_learning_cycle,verify_learning_cycle_result
class T(unittest.TestCase):
 def test_chain(self):
  g=genesis_incremental_state();b=assemble_runtime_batch((build_runtime_input(101,'crypto_verified_learned_case','o1','a'*64,{'probability':None}),build_runtime_input(105,'crypto_verified_learned_case','o2','b'*64,{'probability':None})));r,s=run_learning_cycle(1,g,b);print('[STATE]',g.applied_through_sequence,'->',s.applied_through_sequence);self.assertTrue(verify_learning_cycle_result(r));self.assertTrue(verify_incremental_state(s));self.assertEqual(s.parent_state_hash,g.state_hash)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-215 frozen OCL-027/028 transition certified')
