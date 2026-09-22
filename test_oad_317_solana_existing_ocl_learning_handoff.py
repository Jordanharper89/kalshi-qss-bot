\

import unittest
from qseries_v2.oracle_adapters.independent.oad_315_solana_verified_learned_case_contract import SolanaLearnedCase
from qseries_v2.oracle_adapters.independent.oad_317_solana_existing_ocl_learning_handoff import *
def c(i,o):
 return SolanaLearnedCase(i,i,"X","P",15,(("price","RISING"),),o,.1,("a",),i,True,False)
class T(unittest.TestCase):
 def test_hold(self):
  x=build_solana_learning_handoff(())
  self.assertEqual(x.state,"HOLD_VERIFIED_OUTCOMES_REQUIRED")
 def test_ready(self):
  x=build_solana_learning_handoff((c("1","UP"),c("2","DOWN")))
  print("[HANDOFF]",x.state,x.learned_cases,x.evidence_hash)
  self.assertEqual(x.state,"READY_FOR_EXISTING_OCL_LEARNING")
  self.assertIsNone(x.probability); self.assertIsNone(x.direction)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-317 Solana verified learned cases admitted toward existing OCL architecture")
 print("[PASS] no separate Solana learner created")

