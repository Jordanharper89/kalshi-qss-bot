import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_216_crypto_scientific_reasoning_handoff_gate as m
class T(unittest.TestCase):
 def test_missing_holds(self):
  s=SimpleNamespace(state_hash='a'*64,applied_through_sequence=100)
  with patch.object(m,'read_crypto_ocl_state',return_value=(1,s,'b'*64)):r=m.evaluate_crypto_scientific_reasoning_handoff()
  print('[GATE]',r.state);print('[MISSING]',r.missing_state_hashes);self.assertEqual(r.state,'HOLD_CERTIFIED_NON_LEARNER_STATE_HASHES_REQUIRED');self.assertIsNone(r.handoff);self.assertTrue(r.physical_ready)
 def test_complete_uses_ocl029(self):
  s=SimpleNamespace(state_hash='a'*64,applied_through_sequence=100);h={n:'b'*64 for n in m.REQUIRED_NON_LEARNER_HASHES}
  with patch.object(m,'read_crypto_ocl_state',return_value=(1,s,'c'*64)):r=m.evaluate_crypto_scientific_reasoning_handoff(certified_state_hashes=h)
  self.assertTrue(r.handoff_verified);self.assertFalse(r.handoff.execution_allowed);self.assertFalse(r.handoff.publication_allowed)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-216 truthful OCL-029 handoff gate certified')
