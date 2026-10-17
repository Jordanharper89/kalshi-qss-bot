import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_post_lock_ata(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("MRY021_POST_LOCK_ATA",s)
  self.assertIn("_reverse_instruction_sets(",s)
  self.assertIn("_reverse_prepend_ata_readiness(USER,out)",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":unittest.main(verbosity=2)
