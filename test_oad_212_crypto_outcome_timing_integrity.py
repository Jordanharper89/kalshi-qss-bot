import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_187_crypto_exact_horizon_coinbase_outcome as a
from qseries_v2.oracle_adapters.independent import oad_188_crypto_verified_learned_case_postgresql_persistence as b
class T(unittest.TestCase):
 def e(self):return SimpleNamespace(experience_id='e1',asset='BTC',snapshot_at='2026-08-31T10:00:00+00:00',condition_vector=(('coinbase','spot_price',100.0,'OBSERVED'),),temporal_vector=(),evidence_hash='a'*64,condition_hash='b'*64,experience_hash='c'*64,lineage_hash='d'*64)
 def test_open_and_truth(self):
  with patch.object(a,'_coinbase_candles',return_value=((1788170460,90,110,101,109,1),)):
   x=a.acquire_exact_coinbase_outcome(self.e(),60)
  print('[PRICE]',x.outcome_price,'[OFFSET]',x.timing_offset_seconds);self.assertEqual(x.outcome_price,101.0);self.assertTrue(x.exact_interval)
 def test_late_not_exact(self):
  with patch.object(a,'_coinbase_candles',return_value=((1788170520,90,110,102,109,1),)):
   x=a.acquire_exact_coinbase_outcome(self.e(),60)
  c=b.canonicalize_verified_learned_case(self.e(),x);p=dict(c.payload);print('[REALIZED]',p['realized_horizon_seconds'],'[EXACT]',p['exact_interval']);self.assertFalse(p['exact_interval']);self.assertEqual(p['timing_offset_seconds'],60);self.assertIsNone(p['probability']);self.assertFalse(c.execution_allowed)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-212 truthful timing integrity certified')
