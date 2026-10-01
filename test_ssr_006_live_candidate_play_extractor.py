import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_006_live_candidate_play_extractor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_extract(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"candidate_count":d["candidate_count"],"max_age_seconds":d["max_age_seconds"]},sort_keys=True))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  self.assertIsInstance(d["plays"],list)
  print("[PASS] SSR-006 live candidate play extractor")
  print("[INFO] candidate_count may be zero if no recent live capture exists yet")
if __name__=="__main__":unittest.main()
