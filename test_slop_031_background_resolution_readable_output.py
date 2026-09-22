import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import UnresolvedView
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output import resolve_background
class T(unittest.TestCase):
 def test_resolution_print(self):
  p=SimpleNamespace(prediction_id="P");e=SimpleNamespace(prediction_id="P",outcome="TARGET_FIRST",gross_return=.11,net_return=.09,friction_bps=200,terminal_return=.08,mfe=.12,mae=-.01)
  u=UnresolvedView((p,),("P",),("T",),(),False);lines=[]
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.unresolved_view",return_value=u),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.materialize_frozen_prediction_path",return_value=object()),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.resolve_economics",return_value=e),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_031_background_resolution_readable_output.persist_resolutions"):
   x=resolve_background(progress=lines.append)
  print("\n".join(lines));self.assertEqual(x["resolved"],1);self.assertIn("[ORACLE RESOLUTION]",lines)
if __name__=="__main__":unittest.main(verbosity=2)
