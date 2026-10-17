import ast,unittest
from pathlib import Path
M=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_011_reverse_readiness.py")

class T(unittest.TestCase):
 def test_direct_refresh(self):
  s=M.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn('prebuild_sell_templates',s)
  self.assertIn('[MRY022_REVERSE_REFRESH]',s)
  self.assertNotIn('rt.run(',s)
  self.assertNotIn('inspect.',s)

 def test_runtime_guards_preserved(self):
  s=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py").read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
