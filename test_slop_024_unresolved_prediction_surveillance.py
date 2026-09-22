import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import unresolved_view
class T(unittest.TestCase):
 def test_resolved_removed(self):
  ps=(SimpleNamespace(prediction_id="A",token_address="TA"),SimpleNamespace(prediction_id="B",token_address="TB"))
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance.read_predictions",return_value=ps),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance.read_resolution_dicts",return_value=({"prediction_id":"A"},)):
   x=unresolved_view()
  print("[SLOP-024]",x);self.assertEqual(x.prediction_ids,("B",));self.assertEqual(x.tokens,("TB",))
if __name__=="__main__":unittest.main(verbosity=2)
