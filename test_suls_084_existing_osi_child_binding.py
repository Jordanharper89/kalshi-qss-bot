import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"run_osi_solana_intelligence_live.py"
class T(unittest.TestCase):
 def test_binding(self):
  s=P.read_text(encoding="utf-8")
  self.assertEqual(s.count("run_suls_forever"),2)
  self.assertIn('name="OSI-SULS-EventDriven"',s)
  self.assertIn("daemon=True",s)
  self.assertIn("EXECUTION_AUTHORITY=False",s)
  print("[PASS] SULS-084 existing OSI child event-driven binding")
  print("[PASS] no new top-level Solana child")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
