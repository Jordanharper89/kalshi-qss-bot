import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_027_physical_profitability_generalization_report import physical_report
class T(unittest.TestCase):
 def test_multitoken_gate(self):
  ps=tuple(SimpleNamespace(prediction_id=str(i),token_address="T"+str(i%3)) for i in range(15))
  rs=tuple({"prediction_id":str(i),"outcome":"TARGET_FIRST","net_return":.01} for i in range(15))
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_027_physical_profitability_generalization_report.read_predictions",return_value=ps),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_027_physical_profitability_generalization_report.read_resolution_dicts",return_value=rs):
   x=physical_report()
  print("[SLOP-027]",x);self.assertEqual(x.state,"MULTI_TOKEN_POSITIVE_NET_EXPECTANCY_FOUND");self.assertEqual(x.independent_tokens,3)
if __name__=="__main__":unittest.main(verbosity=2)
