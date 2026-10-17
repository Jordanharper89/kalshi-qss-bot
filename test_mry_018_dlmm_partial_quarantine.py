import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_quarantine(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("[MRY018_DLMM_QUARANTINE]",s)
  self.assertIn('READY_TOKENS.discard(str(token))',s)
  self.assertIn('"DLMM_PARTIAL" in msg',s)
 def test_money_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":
 unittest.main(verbosity=2)
