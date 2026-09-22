import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel import EconomicFunnel
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_022_first_prospective_profitability_gate import prospective_profitability_gate
class T(unittest.TestCase):
 def test_truthful_states(self):
  cases=((5,.1,"INSUFFICIENT_PHYSICAL_SUPPORT",False),(20,.01,"POSITIVE_NET_EXPECTANCY_OBSERVED",True),(20,-.01,"NONPOSITIVE_NET_EXPECTANCY_OBSERVED",False))
  for n,e,s,c in cases:
   with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_022_first_prospective_profitability_gate.economic_funnel",return_value=EconomicFunnel(n,n,0,0,n,0,e,False)):
    x=prospective_profitability_gate(min_resolved=15);print("[SLOP-022]",x);self.assertEqual((x.state,x.profitability_claimed),(s,c))
if __name__=="__main__":unittest.main(verbosity=2)
