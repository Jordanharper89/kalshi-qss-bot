import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_028_oracle_live_buy_pressure_child_boundary import live_child_pass
class T(unittest.TestCase):
 def test_child_boundary(self):
  p=SimpleNamespace(prediction_id="P")
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_028_oracle_live_buy_pressure_child_boundary.current_buy_pressure_admission",return_value={"admitted":(p,)}),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_028_oracle_live_buy_pressure_child_boundary.persist_predictions") as save:
   x=live_child_pass("TOKEN")
  print("[SLOP-028]",x);save.assert_called_once();self.assertEqual(x.state,"BUY_PRESSURE_ADMITTED");self.assertFalse(x.execution_authority)
if __name__=="__main__":unittest.main(verbosity=2)
