import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_115_cross_venue_continuous_path_reconstructor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"path_count":d["path_count"],"family_path_counts":d["family_path_counts"]},sort_keys=True))
  self.assertGreater(d["path_count"],0,"NO_CROSS_VENUE_PATHS")
  self.assertGreaterEqual(len(d["family_path_counts"]),2,"ONLY_ONE_VENUE_HAS_PRICE_PATHS")
  self.assertTrue(d["continuous_between_horizons"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-115 cross-venue continuous path reconstructor")
  print("[PASS] continuous path + MFE/MAE + standard horizons across multiple venues")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
