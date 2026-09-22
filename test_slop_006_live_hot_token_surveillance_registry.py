import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_006_live_hot_token_surveillance_registry import HotTokenRegistry
class T(unittest.TestCase):
 def test_registry(self):
  r=HotTokenRegistry();r.refresh(("A","B"));x=r.refresh(("B","C"))
  print("[SLOP-006]",x)
  self.assertEqual(set(r.tokens()),{"A","B","C"});self.assertEqual([z for z in x if z.token_address=="B"][0].discoveries,2)
if __name__=="__main__":unittest.main(verbosity=2)
