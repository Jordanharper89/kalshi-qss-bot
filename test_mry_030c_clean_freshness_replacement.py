import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_runtime(self):
  s=R.read_text(); ast.parse(s)
  a=s.index("def _fast_010_refresh_latest")
  b=s.index("def fast_live_attack",a)
  f=s[a:b]
  self.assertEqual(f.count("lane.latest.get(token)"),1)
  self.assertEqual(f.count("exact_snapshot_opportunities"),1)
  self.assertNotIn("while refreshes<",f)
  self.assertIn("FAST_010_SINGLE_REFRESH",f)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__": unittest.main(verbosity=2)
