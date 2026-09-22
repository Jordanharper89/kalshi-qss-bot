\

import unittest
from qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation
from qseries_v2.oracle_adapters.independent.oad_313_solana_outcome_pending_temporal_cases import SolanaOutcomePendingCase
from qseries_v2.oracle_adapters.independent.oad_314_solana_verified_forward_outcome_attribution import *
def row(i,t,p):
 return SolanaHistoricalObservation(i,"S","solana_token_pool_identity_liquidity",t,None,"dex","X",{"token_address":"X","pools":({"pair_address":"P","price_usd":p},)})
class T(unittest.TestCase):
 def test_outcome(self):
  c=SolanaOutcomePendingCase("e","X","P","2026-09-01T00:00:05+00:00",(("price","RISING"),),("a","b"),15)
  x=attribute_forward_outcomes((c,),(row("a","2026-09-01T00:00:00+00:00",1),row("b","2026-09-01T00:00:05+00:00",1.1),row("c","2026-09-01T00:00:20+00:00",1.21)))
  print("[OUTCOME]",x[0].outcome_class,x[0].return_fraction)
  self.assertTrue(x[0].verified); self.assertEqual(x[0].outcome_class,"UP")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-314 exact future-observation Solana outcome attribution certified")

