import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_116c_repaired_cross_venue_continuous_paths import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"path_count":d["path_count"],
   "family_path_counts":d["family_path_counts"]},sort_keys=True))
  self.assertGreater(d["path_count"],0,"NO_REPAIRED_CROSS_VENUE_PATHS")
  self.assertEqual(len(d["family_path_counts"]),14,
   "NOT_ALL_14_CERTIFIED_FAMILIES_HAVE_REPAIRED_PATHS")
  self.assertTrue(d["continuous_between_horizons"])
  self.assertEqual(d["identity_policy"],"DIRECTED_ASSET_PAIR_PRESERVED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-116C repaired cross-venue continuous paths")
  print("[PASS] all 14 certified venue families have price-path materialization")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
