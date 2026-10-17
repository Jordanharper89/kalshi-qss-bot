import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_alignment(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("ac[11][\"pubkey\"]=token_program",s)
  self.assertIn("ac[12][\"pubkey\"]=q87.c.TOKEN",s)
  self.assertIn("_mry019_align_meteora_programs(route)",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
