import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_159_phase8_enriched_feature_snapshots import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  fam=len({x["family"] for x in d["snapshots"]})
  print("[STATE]",json.dumps({"snapshot_count":d["snapshot_count"],
   "family_count":fam,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["snapshot_count"],0)
  self.assertGreater(fam,0)
  self.assertEqual(d["future_leakage"],"FORBIDDEN")
  self.assertTrue(all(x["feature_rows_after_cutoff"]==0 for x in d["snapshots"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-159 enriched leakage-safe feature snapshots")
  print("[PASS] price, trade velocity and volume features frozen before outcome")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
