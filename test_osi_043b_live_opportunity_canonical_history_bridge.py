import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_043_live_opportunity_to_historical_formula_bridge import bridge
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=bridge(ROOT);self.assertFalse(d["execution_authority"]);self.assertTrue(d["future_data_excluded"])
  print("[ASSET]",d["asset_key"]);print("[SOURCE_TABLE]",d["source_table"]);print("[HISTORICAL_ROWS]",d["historical_rows"]);print("[COMPARABLE_CASES]",d["comparable_case_count"])
  if d["historical_rows"]<=0:self.fail("NO_CANONICAL_HISTORY_READ")
  print("[PASS] OSI-043B live opportunity -> canonical history bridge")
  print("[TRADER] A real Solana opportunity can now look backward into Oracle's canonical warehouse without future leakage")
if __name__=="__main__":unittest.main()
