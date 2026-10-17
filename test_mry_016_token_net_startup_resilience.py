import ast,unittest
from pathlib import Path
Q=Path("qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py")
class T(unittest.TestCase):
 def test_resilience(self):
  s=Q.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("[ORACLE025_TOKEN_WARM_RETRY]",s)
  self.assertIn("[ORACLE025_TOKEN_WARM_SKIP]",s)
  self.assertIn('"fetch failed" in text',s)
 def test_no_execution_change(self):
  s=Q.read_text(encoding="utf-8")
  self.assertIn("EXECUTION_AUTHORITY=False",s)
  self.assertIn("PAPER_ONLY=True",s)
if __name__=="__main__":unittest.main(verbosity=2)
