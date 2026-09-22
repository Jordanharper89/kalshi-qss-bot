import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild import PendingSurveillancePlan
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild import lifecycle_pass
class T(unittest.TestCase):
 def test_new_and_pending_coexist(self):
  p=ProspectiveOpportunity("P","NEW","PAIR","2026-09-17T15:30:00+00:00",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
  def admit(t,**k):return {"admitted":(p,) if t=="NEW" else ()}
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild.current_buy_pressure_admission",side_effect=admit),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild.persist_predictions",return_value={"total":2,"new":1,"existing":0}),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_015b_concurrent_live_lifecycle_rebuild.pending_surveillance_plan",return_value=PendingSurveillancePlan(("OLD","P"),("OLDTOKEN","NEW"),False)):
   x=lifecycle_pass(("NEW","HOT"))
  print("[SLOP-015B]",x)
  self.assertEqual(x["evaluated"],2);self.assertEqual(x["admitted"],1)
  self.assertEqual(x["surveillance_tokens"],("HOT","NEW","OLDTOKEN"));self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
