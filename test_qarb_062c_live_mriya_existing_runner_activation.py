import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062c_live_mriya_existing_runner_activation as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_lane(self):q.install_lane();self.assertIs(q.wv.q60b.p.SimulationLane,q.ml.MriyaPaperLane)
if __name__=="__main__":unittest.main(verbosity=2)
