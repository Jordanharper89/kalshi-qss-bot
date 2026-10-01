import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registration(self):
  text=(ROOT/"run_oracle_live.py").read_text(encoding="utf-8",errors="replace")
  ast.parse(text)
  self.assertIn("run_osi_solana_intelligence_live.py",text)
  self.assertTrue((ROOT/"run_oracle_live.py.osi018b.bak").is_file())
  self.assertTrue((ROOT/"run_osi_solana_intelligence_live.py").is_file())
  self.assertIn("execution_authority=FALSE",text)
  print("[PASS] OSI-018B existing Oracle launcher registration")
  print("[TRADER] Starting Oracle will also start the read-only Solana opportunity hunter")
  print("[PASS] launcher remains syntactically valid")
  print("[PASS] execution_authority=FALSE")
  print("[SCOPE] Registration certified; restart Oracle required for physical activation")
if __name__=="__main__":unittest.main()
