import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel import economic_funnel
class T(unittest.TestCase):
 def test_accounting(self):
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel.read_predictions",return_value=(1,2,3)),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel.read_resolution_dicts",return_value=({"outcome":"TARGET_FIRST","net_return":.08},{"outcome":"STOP_FIRST","net_return":-.07})):
   x=economic_funnel()
  print("[SLOP-021]",x);self.assertEqual((x.frozen,x.resolved,x.unresolved),(3,2,1));self.assertAlmostEqual(x.net_expectancy,.005)
if __name__=="__main__":unittest.main(verbosity=2)
