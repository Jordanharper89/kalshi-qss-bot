import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_025_dedicated_solana_opportunity_runtime_boundary import activate,REL,DIRS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_boundary(self):
  d=activate(ROOT);base=ROOT/REL
  for x in DIRS:self.assertTrue((base/x).is_dir())
  self.assertEqual(d["primary_sources"],["NATIVE_SOLANA","GMGN"]);self.assertFalse(d["execution_authority"])
  print("[PASS] OSI-025 dedicated Solana opportunity runtime boundary")
  print("[RUNTIME]",base)
  print("[TRADER] Solana opportunity state is isolated from general Oracle runtime noise")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
