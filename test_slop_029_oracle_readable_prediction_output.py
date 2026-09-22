import unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_029_oracle_readable_prediction_output import prediction_lines
class T(unittest.TestCase):
 def test_readable(self):
  p=SimpleNamespace(token_address="T",pair_address="PAIR",frozen_at="NOW",horizon_seconds=60,target=.1,stop=.05,friction_bps=200,prediction_id="P",state="PENDING_60S")
  x=prediction_lines(p,1.25);print("\n".join(x))
  self.assertIn("[ORACLE PREDICTION]",x);self.assertIn("Execution Authority: FALSE",x)
if __name__=="__main__":unittest.main(verbosity=2)
