import unittest
from unittest.mock import patch
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent import oad_182_crypto_persisted_experience_exact_readback as a
from qseries_v2.oracle_adapters.independent import oad_189_crypto_learned_case_exact_history_readback as b
class Cur:
 def __init__(self,rows):self.rows=rows;self.sql=''
 def __enter__(self):return self
 def __exit__(self,*x):return False
 def execute(self,s,args=None):
  if 'SELECT sequence_number' in s:self.sql=s
 def fetchall(self):return self.rows
class Conn:
 def __init__(self,rows):self.c=Cur(rows)
 def __enter__(self):return self
 def __exit__(self,*x):return False
 def cursor(self):return self.c
 def rollback(self):pass
class T(unittest.TestCase):
 def test_latest_experience(self):
  p={'experience_id':'e','asset':'BTC','snapshot_at':'x','cohort_state':'FULL_COVERAGE','condition_vector':(),'temporal_vector':(),'evidence_hash':'a'*64,'condition_hash':'b'*64,'experience_hash':'c'*64,'lineage_hash':'d'*64,'outcome_attached':False};c=Conn([(900,'o','source.crypto.experience.btc','crypto_historical_experience_candidate',datetime.now(timezone.utc),p)])
  with patch.object(a,'connect',return_value=c):r=a.read_persisted_crypto_experiences(assets=('BTC',),per_asset_limit=16)
  print('[SEQ]',r.records[0].sequence_number);self.assertIn('ORDER BY sequence_number DESC',c.c.sql)
 def test_legacy_cannot_claim_exact(self):
  p={'asset':'BTC','experience_id':'old','snapshot_at':'x','condition_vector':(),'temporal_vector':(),'condition_hash':'a'*64,'experience_hash':'b'*64,'lineage_hash':'c'*64,'horizon_seconds':60,'outcome_observed_at':'y','return_fraction':.01,'return_percent':1,'outcome_hash':'d'*64,'learning_event_hash':'e'*64,'exact_interval':True};c=Conn([(901,'o','crypto_verified_learned_case',p)])
  with patch.object(b,'connect',return_value=c):r=b.read_crypto_learned_case_history(assets=('BTC',),per_asset_limit=16)
  print('[LEGACY]',r[0].legacy_timing,'[EXACT]',r[0].exact_interval);self.assertTrue(r[0].legacy_timing);self.assertFalse(r[0].exact_interval);self.assertIn('ORDER BY sequence_number DESC',c.c.sql)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T));
 if not r.wasSuccessful():raise SystemExit(1)
 print('[PASS] OAD-213 latest-by-source history certified')
