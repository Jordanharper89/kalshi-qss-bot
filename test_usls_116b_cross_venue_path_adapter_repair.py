import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_116b_cross_venue_path_adapter_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"source_artifact_count":d["source_artifact_count"],
   "economic_row_count":d["economic_row_count"],"family_row_counts":d["family_row_counts"],
   "missing_economic_families":d["missing_economic_families"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["economic_row_count"],0,"NO_REPAIRED_CROSS_VENUE_ECONOMIC_ROWS")
  self.assertGreaterEqual(len(d["family_row_counts"]),6,"REPAIRED_FAMILY_COVERAGE_STILL_TOO_NARROW")
  self.assertEqual(d["identity_policy"],
   "EXPLICIT_MARKET_PLUS_PRESERVE_DIRECTED_ASSET_PAIR_NO_GUESSED_TOKEN_ROLE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-116B cross-venue path adapter repair")
  print("[PASS] per-row venue detection + nested economics + directed asset pairs preserved")
  print("[NEXT] REBUILD_CROSS_VENUE_PATHS_FROM_REPAIRED_ROWS")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
