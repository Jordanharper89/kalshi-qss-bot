import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_swap2_layout(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn('mint_x=str(ac[7]["pubkey"])',s)
  self.assertIn('mint_y=str(ac[8]["pubkey"])',s)
  self.assertNotIn('mint_x=str(ac[6]["pubkey"])',s)
  self.assertIn('ac[11]["pubkey"]=token_program',s)
  self.assertIn('ac[12]["pubkey"]=token_program',s)

 def test_live_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("FAST_010_MIN_REALIZED_LAMPORTS=10_000",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
