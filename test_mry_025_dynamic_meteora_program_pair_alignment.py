import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_dynamic_alignment(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("METEORA_TEMPLATES.get(token)",s)
  self.assertIn("MRY025_TOKEN_PROGRAM_PAIR_AMBIGUOUS",s)
  self.assertIn('ac[i]["pubkey"]=want_x',s)
  self.assertNotIn('mint_x=str(ac[7]["pubkey"])',s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":unittest.main(verbosity=2)
