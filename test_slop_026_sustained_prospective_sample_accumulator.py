import unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_021_live_economic_funnel import EconomicFunnel
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_026_sustained_prospective_sample_accumulator import accumulate
class T(unittest.TestCase):
 def test_accumulates_without_maturity_block(self):
  f=EconomicFunnel(2,1,1,0,0,1,.08,False)
  with patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_026_sustained_prospective_sample_accumulator.worker_round",return_value={"admitted":1,"resolution_new":0}),patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_026_sustained_prospective_sample_accumulator.economic_funnel",return_value=f):
   x=accumulate(rounds=3,delay_seconds=0)
  print("[SLOP-026]",x);self.assertEqual(x["admitted_this_run"],3);self.assertEqual(x["funnel"].resolved,1)
if __name__=="__main__":unittest.main(verbosity=2)
