import ast,unittest
from pathlib import Path

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
 def test_runtime_parses(self):
  ast.parse(R.read_text(encoding="utf-8"))

 def test_exact_xy_slots(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn('x_mint=str(ac[6].get("pubkey") or "")',f)
  self.assertIn('y_mint=str(ac[7].get("pubkey") or "")',f)
  self.assertIn('ac[11]["pubkey"]=x_program',f)
  self.assertIn('ac[12]["pubkey"]=y_program',f)
  self.assertNotIn("hits=[]",f)
  self.assertNotIn("target_is_x",f)

 def test_program_source_is_physical_pump_layout(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def _mry019_align_meteora_programs")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn('pa[3].get("pubkey")',f)
  self.assertIn('pa[4].get("pubkey")',f)
  self.assertIn('pa[11].get("pubkey")',f)
  self.assertIn('pa[12].get("pubkey")',f)

 def test_money_guards_preserved(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
  self.assertIn("FAST_010_6040_CHAIN_TRUTH",s)

if __name__=="__main__":
 unittest.main(verbosity=2)
