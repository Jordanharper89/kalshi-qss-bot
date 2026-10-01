import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q

class T(unittest.TestCase):
 def test_persist(self):
  with tempfile.TemporaryDirectory() as d:
   x=q.observe(Path(d),{"token":"TOK","horizon_seconds":2,"paper_net_sol":.01})
   self.assertEqual(x["status"],"ACTIVE")

 def test_guard_survives_061b_install(self):
  q.install()
  q.wv.install()
  self.assertIs(q.wv.q60b.p.SimulationLane,q.ActiveProfitLane)

 def test_exact_live_lane(self):
  q.install()
  self.assertIs(q.q65.p.SimulationLane,q.ActiveProfitLane)

 def test_mode(self):
  self.assertTrue(q.PAPER_ONLY)
  self.assertFalse(q.EXECUTION_AUTHORITY)
  self.assertFalse(q.REAL_MONEY_MOVED)

if __name__=="__main__":
 unittest.main(verbosity=2)
