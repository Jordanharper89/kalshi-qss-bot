\

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_325_solana_universal_single_writer_persistence as m
class T(unittest.TestCase):
 def test_queue_only(self):
  cov=SimpleNamespace(transactions=2,observations=(object(),object(),object()),state="UNIVERSAL_BATCH_ACCOUNTED")
  sub=SimpleNamespace(request_id="rid")
  with patch.object(m,"build_universal_coverage_batch",return_value=cov),patch.object(m,"submit_observation_batch",return_value=sub) as s,patch.object(m,"await_request",return_value=(SimpleNamespace(accepted=True),)*3):
   x=m.persist_solana_universal_chain_batch(root=".")
  print("[PERSIST]",x.transactions,x.observations,x.committed_events,x.request_id)
  self.assertEqual(x.committed_events,3);s.assert_called_once()
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-325 Solana universal observations admitted only through OPH-019")

