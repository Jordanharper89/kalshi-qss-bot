import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_006_discovery_latency_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_truth(self):
  p,d=write(ROOT)
  print("[MIN_SECONDS]",d["min_seconds"]);print("[MEDIAN_SECONDS]",d["median_seconds"])
  print("[LAUNCH_GRADE_BIRTH_SENSOR]",d["launch_grade_birth_sensor"]);print("[CLASSIFIED_ROLE]",d["classified_role"])
  self.assertEqual(d["classified_role"],"ENRICHMENT_DISCOVERY_ONLY")
  print("[PASS] SULS-006 discovery latency truth gate")
if __name__=="__main__":unittest.main()
