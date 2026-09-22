import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_155_phase8_leakage_safe_feature_snapshot_extractor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"snapshot_count":d["snapshot_count"],
   "future_leakage":d["future_leakage"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["snapshot_count"],0,"NO_LEAKAGE_SAFE_FEATURE_SNAPSHOTS")
  self.assertEqual(d["future_leakage"],"FORBIDDEN")
  self.assertTrue(all(x["future_rows_used_in_features"]==0 for x in d["snapshots"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-155 leakage-safe feature snapshot extractor")
  print("[PASS] feature snapshots use only information available at/before cutoff")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
