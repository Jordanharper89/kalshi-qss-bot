import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_010b_viable_pool_surveillance_rebuild import certify
class T(unittest.TestCase):
 def test_physical(self):
  x=certify(hot_limit=5,rounds=14,delay_seconds=5.0,refresh_every=3)
  print("[SLOP-010B]",{k:v for k,v in x.items() if k!="states"})
  self.assertGreater(x["refreshes"],1);self.assertGreater(x["observations"],0)
  self.assertGreater(x["tracked"],0);self.assertGreater(x["ready_60s"],0)
  self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
