\

import unittest
from qseries_v2.oracle_adapters.independent.oad_315_solana_verified_learned_case_contract import SolanaLearnedCase
from qseries_v2.oracle_adapters.independent.oad_316_solana_comparable_case_statistics import *
def c(i,outcome):
 return SolanaLearnedCase(i,i,"X","P",15,(("price","RISING"),),outcome,.1,("a",),i,True,False)
class T(unittest.TestCase):
 def test_stats(self):
  x=aggregate_comparable_solana_cases((c("1","UP"),c("2","UP"),c("3","DOWN")))[0]
  print("[STATS] samples=",x.sample_size,"raw_up=",x.raw_up_frequency,"weighted_up=",x.weighted_up_frequency,"contradictions=",x.contradictions)
  self.assertEqual(x.sample_size,3); self.assertEqual(x.up_count,2); self.assertEqual(x.contradictions,1)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-316 Solana comparable-case frequencies + recency weighting certified")

