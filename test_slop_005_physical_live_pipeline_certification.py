import unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_005_physical_live_pipeline_certification import certify_live_pipeline
class T(unittest.TestCase):
 def test_physical(self):
  x=certify_live_pipeline(scan_limit=5); print("[SLOP-005]",x)
  self.assertGreater(x["discovered"],0); self.assertGreater(x["scanned"],0)
  self.assertEqual(x["observed"],x["scanned"]); self.assertEqual(x["state"],"LIVE_OPPORTUNITY_PIPELINE_ACTIVE")
  self.assertFalse(x["execution_authority"])
  print("[NOTE] admitted=0 is valid when no fresh BUY_PRESSURE opportunity exists during this scan")
if __name__=="__main__": unittest.main(verbosity=2)
