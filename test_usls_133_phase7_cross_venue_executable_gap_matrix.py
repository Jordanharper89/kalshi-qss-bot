import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_133_phase7_cross_venue_executable_gap_matrix import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"fully_supported_family_count":d["fully_supported_family_count"],
   "fully_supported_families":d["fully_supported_families"],
   "gap_families":d["gap_families"],"families":d["families"]},sort_keys=True))
  self.assertEqual(len(d["families"]),14)
  self.assertGreater(d["fully_supported_family_count"],0,"NO_VENUE_HAS_FULL_EXECUTABLE_INPUT_SUPPORT")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-133 cross-venue executable gap matrix")
  print("[PASS] all 14 certified venue families measured against same executable-input contract")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
