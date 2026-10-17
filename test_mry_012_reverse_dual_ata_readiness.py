import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_dual_ata(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("create_wsol_ata=_ata_create_idempotent_ix",s)
  self.assertIn("[create_wsol_ata,create_token_ata]+ixs",s)
  self.assertIn("q87.c.WSOL,q87.c.TOKEN",s)
 def test_money_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
