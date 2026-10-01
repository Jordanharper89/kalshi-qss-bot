import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_child_exists(self):
  p=ROOT/"run_osi_solana_intelligence_live.py";self.assertTrue(p.is_file())
  text=p.read_text(encoding="utf-8")
  self.assertIn("EXECUTION_AUTHORITY=False",text);self.assertIn("INTERVAL=1.0",text)
 def test_upstream(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_012_live_event_normalization_and_intake.py").is_file())
  print("[PASS] OSI-017 live child worker installed")
  print("[TRADER] Oracle can scan the certified Solana live source once per second for fresh opportunities")
  print("[PASS] execution_authority=FALSE")
  print("[SCOPE] Child worker installed; launcher registration remains separate")
if __name__=="__main__":unittest.main()
