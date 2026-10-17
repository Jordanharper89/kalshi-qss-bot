
import unittest, tempfile
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_149_atomic_simulation_boundary as m
class Tests(unittest.TestCase):
 def test_sensitive_calls_detected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.py';p.write_text('def simulate_current(tx):\n    return signer.signed_tx(tx)\n')
   x=m.inspect_file(p,('simulate_current',))
   self.assertEqual(x['targets'][0]['dangerous_calls'],['signer.signed_tx'])
 def test_source_contract(self):
  self.assertEqual(set(m.SOURCES),set(m.TARGETS))
  for x in m.SOURCES.values():self.assertTrue((m.ROOT/x).is_file())
 def test_no_execution_authority(self):
  r=m.run()
  for key in ('direct_simulation_approved','official_verifier_connected','atomic_two_leg_proof_closed','production_cutover','private_key_used','signing','broadcast','scanner_modified'):
   self.assertIs(r[key],False,key)
if __name__=='__main__':unittest.main(verbosity=2)
