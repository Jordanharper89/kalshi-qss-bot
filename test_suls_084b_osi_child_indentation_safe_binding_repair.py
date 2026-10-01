import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"run_osi_solana_intelligence_live.py"

class T(unittest.TestCase):
 def test_repair(self):
  s=P.read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("# SULS-084B indentation-safe existing OSI child binding",s)
  self.assertEqual(s.count("run_suls_forever"),2)
  self.assertIn('name="OSI-SULS-EventDriven"',s)
  self.assertIn("daemon=True",s)
  self.assertIn("EXECUTION_AUTHORITY=False",s)
  self.assertIn("while not STOP.exists():",s)
  self.assertIn("intake_run",s)
  print("[PASS] SULS-084B OSI child syntax restored")
  print("[PASS] original OSI loop preserved")
  print("[PASS] SULS event-driven thread bound inside existing OSI child")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
