import unittest
from qseries_v2.oracle_adapters.independent.oad_215_crypto_ocl_incremental_state_consumption import consume_crypto_learned_cases_into_ocl
class T(unittest.TestCase):
 def test_physical(self):
  r=consume_crypto_learned_cases_into_ocl(limit=512);print('[PHYSICAL] cycle=',r.prior_cycle_sequence,'->',r.new_cycle_sequence);print('[PHYSICAL] through=',r.prior_applied_through_sequence,'->',r.new_applied_through_sequence);print('[PHYSICAL] cases=',r.cases_consumed,'legacy=',r.legacy_timing_cases);print('[PHYSICAL] learner_state_hash=',r.learner_state_hash);print('[PHYSICAL] state=',r.state,'ready=',r.physical_ready);self.assertTrue(r.physical_ready);self.assertEqual(len(r.learner_state_hash),64);self.assertFalse(r.probability_enabled);self.assertFalse(r.execution_authority)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-215 persisted crypto cases consumed into frozen OCL state')
