import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_214_crypto_verified_learned_case_ocl_intake as m
def c(seq,legacy=False):return SimpleNamespace(sequence_number=seq,observation_id=f'o{seq}',asset='BTC',experience_id=f'e{seq}',condition_hash='a'*64,experience_hash='b'*64,lineage_hash='c'*64,outcome_hash='d'*64,learning_event_hash='e'*64,requested_horizon_seconds=60,realized_horizon_seconds=60,timing_offset_seconds=0,timing_certified=not legacy,legacy_timing=legacy,exact_interval=not legacy,return_fraction=.01,horizon_seconds=60)
class T(unittest.TestCase):
 def test_batch_uses_canonical_sequences(self):
  with patch.object(m,'read_crypto_learned_cases_after_sequence',return_value=(c(101),c(105,True))):r=m.build_crypto_ocl_intake(after_sequence=100)
  print('[BATCH]',r.start_sequence,r.end_sequence,'legacy=',r.legacy_timing_cases);self.assertEqual((r.start_sequence,r.end_sequence),(101,105));self.assertTrue(r.intake_ready);self.assertIsNone(r.batch.inputs[0].payload['probability'])
 def test_empty_healthy(self):
  with patch.object(m,'read_crypto_learned_cases_after_sequence',return_value=()):r=m.build_crypto_ocl_intake(after_sequence=105)
  self.assertEqual(r.state,'NO_NEW_CASES');self.assertTrue(r.intake_ready)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-214 crypto learned cases -> frozen OCL-026 intake certified')
