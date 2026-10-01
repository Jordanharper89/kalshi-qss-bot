import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_030_bounded_native_gmgn_physical_reader import read_registered
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=read_registered(ROOT,25,10);self.assertFalse(d["execution_authority"]);self.assertTrue(d["bounded"])
  print("[NATIVE_ROWS]",d["native_rows"]);print("[GMGN_ROWS]",d["gmgn_rows"])
  print("[PASS] OSI-030 bounded native Solana + GMGN physical reader")
  print("[TRADER] Reads only registered physical sources; no recursive scan of the giant Oracle runtime")
  print("[SCOPE] Read-only bounded consumption")
if __name__=="__main__":unittest.main()
