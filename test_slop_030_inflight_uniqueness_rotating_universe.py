import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_024_unresolved_prediction_surveillance import UnresolvedView
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_030_inflight_uniqueness_rotating_universe import admission_universe,rotate
class T(unittest.TestCase):
 def test_guard_rotation(self):
  u=UnresolvedView((),("P",),("B",),(),False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_030_inflight_uniqueness_rotating_universe.unresolved_view",return_value=u):
   x=admission_universe(("A","B","C"),limit=5)
  print("[SLOP-030]",x,rotate(x.candidates,1));self.assertEqual(x.candidates,("A","C"));self.assertEqual(rotate(x.candidates,1),("C","A"))
if __name__=="__main__":unittest.main(verbosity=2)
