import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild import pending_surveillance_plan,observe_pending_tokens
class T(unittest.TestCase):
 def test_unique_pending_tokens(self):
  def p(i,t):return ProspectiveOpportunity(i,t,"PAIR","2026-09-17T15:30:00+00:00",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild.read_predictions",return_value=(p("1","A"),p("2","A"),p("3","B"))),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_014b_pending_token_surveillance_rebuild.observe_hot_round",return_value=("CA","CB")):
   plan=pending_surveillance_plan();x=observe_pending_tokens()
  print("[SLOP-014B]",plan,x)
  self.assertEqual(plan.prediction_ids,("1","2","3"));self.assertEqual(plan.tokens,("A","B"))
  self.assertEqual(x["observed_tokens"],2);self.assertFalse(x["execution_authority"])
if __name__=="__main__":unittest.main(verbosity=2)
