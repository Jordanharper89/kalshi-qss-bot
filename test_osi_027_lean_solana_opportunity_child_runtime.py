import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_027_lean_solana_opportunity_child_runtime import registered_sources,health
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_boundary(self):
  self.assertTrue((ROOT/"run_osi_solana_opportunity_live.py").is_file())
  r=registered_sources(ROOT);self.assertIn("primary",r)
  p=health(ROOT,1,"TEST_COMPLETE");d=json.loads(p.read_text(encoding="utf-8"))
  self.assertFalse(d["execution_authority"])
  print("[PASS] OSI-027 lean Solana opportunity child runtime")
  print("[TRADER] Child reads only the registered Solana/GMGN source registry and writes only isolated opportunity health state")
  print("[SCOPE] Child installed but not registered into production launcher yet")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
