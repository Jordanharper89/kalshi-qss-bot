import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_final_physical_binding(self):
  s=R.read_text();ast.parse(s)
  self.assertIn("{a,b}=={token,wsol}",s)
  self.assertIn("MRY029_FINAL_MINT_PAIR_AMBIGUOUS",s)
  self.assertIn('ac[11]["pubkey"]=target_program if target_is_x else classic',s)
  self.assertIn('ac[12]["pubkey"]=classic if target_is_x else target_program',s)
 def test_post_lock_owner(self):
  s=R.read_text()
  start=s.index("def _fast_010_profit_lock_route")
  end=s.index("\ndef ",start+5)
  f=s[start:end]
  self.assertIn("out=_mry019_align_meteora_programs(out)",f)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":
 unittest.main(verbosity=2)
