\

import unittest
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import SolanaOutcomePendingCase
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import SolanaVerifiedForwardOutcome
from qseries_v2.oracle_adapters.independent.oad_315_solana_verified_learned_case_contract import *
class T(unittest.TestCase):
 def test_case(self):
  c=SolanaOutcomePendingCase("e","X","P","t",(("price","RISING"),),("a","b"),15)
  o=SolanaVerifiedForwardOutcome("e","X","P",15,"t","u",1,1.1,.1,"UP",("a","b","c"),True,False)
  x=build_verified_solana_learned_cases((c,),(o,))[0]
  print("[LEARNED]",x.learned_case_id,x.outcome_class)
  self.assertTrue(x.verified); self.assertEqual(x.outcome_class,"UP")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-315 evidence-grounded Solana learned-case contract certified")

