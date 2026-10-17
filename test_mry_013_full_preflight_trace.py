import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_trace(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("[LIVE_010_PREFLIGHT_FULL]",s)
  self.assertIn("[LIVE_010_PREFLIGHT_REJECT]",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
