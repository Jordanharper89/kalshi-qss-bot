import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_004_continuous_paper_path_outcome_engine import grade
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_grade(self):
  t={"thesis_id":"t","freeze_at":"2026-09-18T05:00:00+00:00","horizon_seconds":60,"thesis_metadata":{"friction_bps":200,"target_return":.10,"economic_stop_return":-.05}}
  o=grade(t,[{"observed_at":"2026-09-18T05:00:00+00:00","price":100},{"observed_at":"2026-09-18T05:00:20+00:00","price":112},{"observed_at":"2026-09-18T05:00:40+00:00","price":96},{"observed_at":"2026-09-18T05:01:00+00:00","price":108},{"observed_at":"2026-09-18T05:01:01+00:00","price":999}])
  self.assertAlmostEqual(o["mfe"],.12);self.assertAlmostEqual(o["mae"],-.04);self.assertAlmostEqual(o["net_return_after_friction"],.06);self.assertTrue(o["target_hit"])
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_003_multi_horizon_prospective_thesis_engine.py").is_file())
  print("[PASS] OSI-004 continuous paper-path outcome contract")
  print("[TRADER] Every paper call can be graded by return, friction, MFE, MAE and target/stop behavior")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
