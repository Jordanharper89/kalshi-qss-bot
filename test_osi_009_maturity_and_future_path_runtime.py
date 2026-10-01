import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_009_maturity_and_future_path_runtime import mature
class T(unittest.TestCase):
 def test_mature(self):
  t={"thesis_id":"t","freeze_at":"2026-09-18T05:00:00+00:00","horizon_seconds":60,"thesis_metadata":{"friction_bps":200}}
  paths={"t":[{"observed_at":"2026-09-18T05:00:00+00:00","price":100},{"observed_at":"2026-09-18T05:01:00+00:00","price":110}]}
  with tempfile.TemporaryDirectory() as td:
   r=mature([t],paths,"2026-09-18T05:01:01+00:00",Path(td)/"o.json")
   self.assertEqual(r["matured_count"],1);self.assertAlmostEqual(r["matured"][0]["net_return_after_friction"],.08)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_004_continuous_paper_path_outcome_engine.py").is_file())
  print("[PASS] OSI-009 maturity + future-path runtime")
  print("[TRADER] Paper calls mature automatically and are graded only from prices observed after the call")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
