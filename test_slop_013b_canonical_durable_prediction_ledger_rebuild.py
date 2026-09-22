import tempfile,unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import persist_predictions,read_predictions

class T(unittest.TestCase):
 def prediction(self,target=.1):
  return ProspectiveOpportunity(
   "P1","T","PAIR","2026-09-17T15:30:00+00:00",
   (("order_flow","BUY_PRESSURE"),),
   60,target,.05,200,"PENDING_60S",False
  )

 def test_restart_safe_idempotent_replay(self):
  with tempfile.TemporaryDirectory() as td:
   p=self.prediction()
   first=persist_predictions((p,),td)

   restarted=read_predictions(td,"PENDING_60S")
   self.assertEqual(len(restarted),1)
   self.assertEqual(restarted[0],p)
   self.assertIsInstance(restarted[0].conditions,tuple)
   self.assertIsInstance(restarted[0].conditions[0],tuple)

   replay=persist_predictions((p,),td)
   final=read_predictions(td,"PENDING_60S")

   print("[SLOP-013B FIRST]",first)
   print("[SLOP-013B RESTART]",restarted)
   print("[SLOP-013B REPLAY]",replay)
   print("[SLOP-013B FINAL]",final)

   self.assertEqual(first["new"],1)
   self.assertEqual(replay["new"],0)
   self.assertEqual(replay["existing"],1)
   self.assertEqual(len(final),1)

 def test_same_id_mutation_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   persist_predictions((self.prediction(),),td)
   with self.assertRaisesRegex(RuntimeError,"immutable prediction collision"):
    persist_predictions((self.prediction(target=.2),),td)

   final=read_predictions(td)
   print("[SLOP-013B COLLISION GUARD]",final)

   self.assertEqual(len(final),1)
   self.assertEqual(final[0].target,.1)

if __name__=="__main__":
 unittest.main(verbosity=2)
