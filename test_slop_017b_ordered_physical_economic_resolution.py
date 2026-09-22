import unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import resolve_economics
class T(unittest.TestCase):
 def p(self):return ProspectiveOpportunity("P","T","PAIR","X",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
 def test_stop_first_is_ordered_not_inferred_from_extrema(self):
  path=SimpleNamespace(anchor_price=100.0,observations=(("20",94.0,"A"),("40",112.0,"B"),("61",111.0,"C")),outcome_at="61",return_fraction=.11,mfe=.12,mae=-.06)
  x=resolve_economics(self.p(),path);print("[SLOP-017B STOP]",x)
  self.assertEqual(x.outcome,"STOP_FIRST");self.assertAlmostEqual(x.gross_return,-.06);self.assertAlmostEqual(x.net_return,-.08)
 def test_target_first(self):
  path=SimpleNamespace(anchor_price=100.0,observations=(("20",111.0,"A"),("40",94.0,"B"),("61",108.0,"C")),outcome_at="61",return_fraction=.08,mfe=.11,mae=-.06)
  x=resolve_economics(self.p(),path);print("[SLOP-017B TARGET]",x)
  self.assertEqual(x.outcome,"TARGET_FIRST");self.assertAlmostEqual(x.net_return,.09)
if __name__=="__main__":unittest.main(verbosity=2)
