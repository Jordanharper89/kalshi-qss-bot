import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_114_strict_cross_venue_economic_row_materializer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"economic_row_count":d["economic_row_count"],
   "family_row_counts":d["family_row_counts"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["economic_row_count"],0,"NO_STRICT_CROSS_VENUE_ECONOMIC_ROWS")
  self.assertGreaterEqual(len(d["family_row_counts"]),2,"CROSS_VENUE_ECONOMIC_COVERAGE_TOO_NARROW")
  self.assertTrue(d["strict_no_guessed_identity"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-114 strict cross-venue economic row materializer")
  print("[PASS] no fabricated token/pool identity; quote-asset agnostic")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
