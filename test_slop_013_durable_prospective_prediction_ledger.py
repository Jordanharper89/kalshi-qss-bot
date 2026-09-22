import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013_durable_prospective_prediction_ledger import persist_predictions,read_predictions
class T(unittest.TestCase):
 def test_restart_safe_identity(self):
  with tempfile.TemporaryDirectory() as td:
   p=ProspectiveOpportunity("P1","T","PAIR","2026-09-17T15:30:00+00:00",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
   a=persist_predictions((p,),td);b=persist_predictions((p,),td);xs=read_predictions(td,"PENDING_60S")
   print("[SLOP-013]",a,b,xs)
   self.assertEqual((a["new"],b["existing"],len(xs)),(1,1,1));self.assertEqual(xs[0],p)
if __name__=="__main__":unittest.main(verbosity=2)
