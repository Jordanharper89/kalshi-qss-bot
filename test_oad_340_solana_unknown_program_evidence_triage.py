\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_340_solana_unknown_program_evidence_triage import *
class T(unittest.TestCase):
 def test_triage(self):
  a=SimpleNamespace(top_level_program_ids=("X","X","TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"),inner_program_ids=("Y",))
  x=triage_unknown_programs((a,))
  print("[TRIAGE]",x.total_unknown,x.top_unknown)
  self.assertEqual(x.total_unknown,3);self.assertEqual(x.top_unknown[0],("X",2))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-340 unresolved program evidence triage certified")

