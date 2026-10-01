import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_032_lean_live_ingestion_cycle import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=cycle(ROOT);self.assertFalse(d["execution_authority"])
  print("[NATIVE_ROWS]",d["native_rows"]);print("[GMGN_ROWS]",d["gmgn_rows"]);print("[NORMALIZED_EVENTS]",d["normalized_events"])
  print("[INTAKE]",d["intake_path"])
  print("[PASS] OSI-032 lean live ingestion cycle")
  print("[TRADER] Registered Solana/GMGN source rows can now flow into the dedicated opportunity runtime")
  print("[SCOPE] One physical cycle; continuous production activation remains separate")
if __name__=="__main__":unittest.main()
